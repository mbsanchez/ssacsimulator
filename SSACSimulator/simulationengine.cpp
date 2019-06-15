/***************************************************************
SSACSimulator application
Copyright (c) 2019, Manuel Sanchez, All rights reserved.

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 3.0 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library.
***************************************************************/
#include "simulationengine.h"
#include <QGVScene.h>
#include <QtDebug>
#include <cmath>
#include <limits>
#include "simulationevent.h"
#include "smartobject.h"
#include "businessprocess.h"

SimulationEngine::SimulationEngine(BusinessProcessModel *processModel, SimulationData *data, QGVScene *scene, QObject *parent)
    : QObject(parent),
      _scene(scene),
      _data(data),
      _currentSpeed(DEFAULT_SPEED),
      _currentTimeMillis(0),
      _lastEvent(-1),
      _processModel(processModel)
{
    _timer.setInterval(DEFAULT_TIME_DELAY);
    connect(&_timer, SIGNAL(timeout()), this, SLOT(nextSimulationStep()));
}

SimulationEngine::~SimulationEngine()
{
    if(isRunning())
        stop();

    clear();
}

bool SimulationEngine::start()
{
    if(_timer.isActive())
        return false;

    if(!simulationParamsAreValid()){
        qInfo() << "Simulation can't be started due to invalid simulation params";
        return false;
    }

    _timer.start();
    emit started();

    return true;
}

void SimulationEngine::pause()
{
    if(!_timer.isActive())
        return;

    _timer.stop();
    emit paused();
}

void SimulationEngine::stop()
{
    _timer.stop();
    clear();
    emit finished();
}

void SimulationEngine::restart()
{
    if(_timer.isActive())
        return;

    stop();
    if(start())
        emit restarted();
}

void SimulationEngine::setCurrentSpeed(uint currentSpeed)
{
    bool active = _timer.isActive();

    if(active)
        _timer.stop();

    _currentSpeed = currentSpeed;

    if(_currentSpeed > MAX_SPEED)
        _currentSpeed = MAX_SPEED;

    if(_currentSpeed < MIN_SPEED)
        _currentSpeed = MIN_SPEED;

    if(active)
        _timer.start();
}

uint SimulationEngine::currentSpeed() const
{
    return _currentSpeed;
}

bool SimulationEngine::isRunning()
{
    return _timer.isActive();
}

void SimulationEngine::nextSimulationStep()
{
    SimulationEvent *event = nullptr;


    event = _data->eventAt(1 + _lastEvent);

    if(event == nullptr){
        stop();
        return;
    }

    ulong dxMillis = static_cast<uint>(_timer.interval()) * _currentSpeed;
    bool processNextEvent = false;
    qulonglong eventStartTime = event->startTimeInMs();

    if(_smartObjects.size()==0){
        _currentTimeMillis = eventStartTime;
    }

    // Check if it is time to process the next event.
    if(_currentTimeMillis + dxMillis  >= eventStartTime){
        dxMillis = static_cast<ulong>(eventStartTime - _currentTimeMillis);
        processNextEvent = true;
    }

    _currentTimeMillis += dxMillis;

    //Process all the events that start at same time
    while (processNextEvent) {
        _lastEvent++;
        emit eventChanged(_lastEvent);
        SmartObject *smo = nullptr;

        //process new events
        if(_smartObjects.contains(event->caseID())){
            smo = _smartObjects[event->caseID()];
            updateAnimationEdge(smo, event);
        } else {
            smo = enterSmartObject(event);
        }

        qDebug() << QString("SMO (BA: %1, EA: %2, ST: %3, TT: %4, CT: %5) is : ").arg(event->beginActor(),
                                                                                     event->endActor(),
                                                                                     QString::number(event->startTime()),
                                                                                     QString::number(event->transitionTime()),
                                                                                     QString::number(_currentTimeMillis))
                << smo->isVisible();

        event = _data->eventAt(1 + _lastEvent);
        if(event == nullptr || _currentTimeMillis != event->startTimeInMs()){
            processNextEvent = false;
        }
    }

    QList<SmartObject*> removeActors;
    // update animations
    for(SmartObject *obj : _smartObjects){
        //Update the object
        obj->nextAnimationStep(dxMillis);

        //Check if the object reached some end actor.
        if(actorIsDone(obj)){
            removeActors.append(obj);
        }
    }

    for(SmartObject *obj : removeActors){
        leaveSmartObject(obj);
    }
}

SmartObject *SimulationEngine::enterSmartObject(SimulationEvent *event)
{
    SmartObject *smo = new SmartObject(event->caseID());
    smo->hide();
    _scene->addItem(smo);
    _smartObjects.insert(event->caseID(), smo);
    updateAnimationEdge(smo, event);

    return smo;
}

void SimulationEngine::updateAnimationEdge(SmartObject *smo, SimulationEvent *event)
{
    BusinessProcessModel::Edge *pEdge = nullptr;

    if(_processModel->edges().contains(event->beginActor())){
        if(_processModel->edges()[event->beginActor()].contains(event->endActor()))
            pEdge = _processModel->edges()[event->beginActor()][event->endActor()];
        else {
            qCritical() << QString("Error: connection: (%1-%2) doesn't exist in the model").arg(event->beginActor(), event->endActor());
        }
    } else {
        qCritical() << QString("Error the actor: '%1' doesn't exist in the model").arg(event->beginActor());
    }

    if(pEdge == nullptr || pEdge->show() == false || pEdge->gvEdge() == nullptr){
        smo->setPathEdge(nullptr, 0);
        smo->setEndActor("");
    }else {
        QGVEdge *gvEdge = pEdge->gvEdge();
        smo->setPathEdge(gvEdge, event->transitionTimeInMs());
        smo->setEndActor(event->endActor());
    }
}

void SimulationEngine::leaveSmartObject(SmartObject *smo)
{
    if(smo == nullptr)
        return;

    qDebug() << QString("The piece %1 has been produced, leaving the system").arg(smo->objectID());

    if(_scene != nullptr)
        _scene->removeItem(smo);

    _smartObjects.remove(smo->objectID());
    delete smo;
}

void SimulationEngine::clear()
{
    for(SmartObject *smo : _smartObjects){
        if(_scene != nullptr)
            _scene->removeItem(smo);

        delete smo;
    }
    _smartObjects.clear();
    _currentTimeMillis = 0;
    _lastEvent = -1;
    _data->restart();
}

bool SimulationEngine::simulationParamsAreValid()
{
    return _processModel != nullptr && _data != nullptr && _scene != nullptr && _data->eventsCount() > 0;
}

bool SimulationEngine::actorIsDone(SmartObject *obj)
{
    if(obj->isAnimationFinished() && _processModel->endActors().contains(obj->endActor())){
        return true;
    }

    return false;
}
