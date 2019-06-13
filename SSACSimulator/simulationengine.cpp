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
#include "simulationevent.h"
#include "smartobject.h"
#include "businessprocess.h"

SimulationEngine::SimulationEngine(BusinessProcessModel *processModel, SimulationData *data, QGVScene *scene, QObject *parent)
    : QObject(parent),
      _scene(scene),
      _data(data),
      _currentSpeed(DEFAULT_SPEED),
      _currentTimeMillis(0),
      _lastEventTimeMillisSinceStart(0),
      _lastEvent(-1),
      _processModel(processModel)
{
    _timer.setInterval(DEFAULT_DELAY);
    connect(&_timer, SIGNAL(timeout()), this, SLOT(nextSimulationStep()));
}

SimulationEngine::~SimulationEngine()
{
    if(isRunning())
        stop();

    clear();
}

void SimulationEngine::start()
{
    if(!simulationParamsAreValid()){
        qInfo() << "Simulation can't be started due to invalid simulation params";
        return;
    }

    _timer.start();
    emit started();
}

void SimulationEngine::pause()
{
    if(!simulationParamsAreValid()){
        qInfo() << "Invalid simulation params detected on pause";
    }

    _timer.stop();
    emit paused();
}

void SimulationEngine::stop()
{
    if(!simulationParamsAreValid()){
        qInfo() << "Invalid simulation params detected on pause";
    }

    _timer.stop();
    clear();
    emit finished();
}

void SimulationEngine::restart()
{
    stop();

    _currentTimeMillis = 0;
    _lastEventTimeMillisSinceStart = 0;
    _lastEvent = -1;
    _data->restart();

    start();
    emit restarted();
}

void SimulationEngine::setCurrentSpeed(float currentSpeed)
{
    _currentSpeed = currentSpeed;
}

float SimulationEngine::currentSpeed() const
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

    bool processNextEvent = false;
    long dxMillis = static_cast<long>(_timer.interval() * _currentSpeed);
    long eventTransitionTime = static_cast<long>(event->startTime() * 60 * 1000);
    long nextEventStartTime = _lastEventTimeMillisSinceStart + eventTransitionTime;

    if(_currentTimeMillis + dxMillis  >= nextEventStartTime){
        dxMillis = nextEventStartTime - _currentTimeMillis;
        processNextEvent = true;
        _lastEvent++;
    }

    _currentTimeMillis += dxMillis;

    if (processNextEvent) {
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
    }

    // update animations
    for(SmartObject *obj : _smartObjects){
        obj->nextAnimationStep(dxMillis);
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

    if(_processModel->edges().contains(event->beginActor()) &&
            _processModel->edges()[event->beginActor()].contains(event->endActor())){
        pEdge = _processModel->edges()[event->beginActor()][event->endActor()];
    }

    if(pEdge == nullptr || pEdge->show() == false || pEdge->gvEdge() == nullptr)
        smo->setPathEdge(nullptr, 0);
    else {
        QGVEdge *gvEdge = pEdge->gvEdge();
        smo->setPathEdge(gvEdge, static_cast<qreal>(event->transitionTime()));
    }
}

void SimulationEngine::exitSmartObject(SmartObject *smo)
{
    if(smo == nullptr)
        return;

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
    _lastEventTimeMillisSinceStart = 0;
    _lastEvent = -1;
}

bool SimulationEngine::simulationParamsAreValid()
{
    return _processModel != nullptr && _data != nullptr && _scene != nullptr && _data->eventsCount() > 0;
}
