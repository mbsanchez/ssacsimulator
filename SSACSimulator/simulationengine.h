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
#ifndef SIMULATIONENGINE_H
#define SIMULATIONENGINE_H

#include <QObject>
#include <QTimer>
#include <QHash>

class QGVScene;
class SimulationData;
class SimulationEvent;
class SmartObject;
class BusinessProcessModel;

class SimulationEngine : public QObject
{
public:
    const float DEFAULT_SPEED = 20.0f; /* 1 min is animated as 1 sec*/
    const int DEFAULT_DELAY = 20;

private:
    Q_OBJECT

public:
    explicit SimulationEngine(BusinessProcessModel *processModel, SimulationData *data, QGVScene *scene, QObject *parent = nullptr);
    ~SimulationEngine();
    bool start();
    void pause();
    void stop();
    void restart();
    void setCurrentSpeed(float currentSpeed);
    float currentSpeed() const;
    bool isRunning();

signals:
    void started();
    void finished();
    void paused();
    void restarted();

protected slots:
    void nextSimulationStep();
    SmartObject* enterSmartObject(SimulationEvent *event);
    void updateAnimationEdge(SmartObject *smo, SimulationEvent *event);
    void leaveSmartObject(SmartObject *smo);
    void clear();
    bool simulationParamsAreValid();
    bool actorIsDone(SmartObject *obj);

private:
    QGVScene *_scene;
    SimulationData *_data;
    QTimer _timer;
    float _currentSpeed;
    long _currentTimeMillis;
    long _lastEventTimeMillisSinceStart;
    long _lastEvent;
    QHash<QString, SmartObject*> _smartObjects;
    BusinessProcessModel *_processModel;
};

#endif // SIMULATIONENGINE_H
