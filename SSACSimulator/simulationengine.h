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
    const uint DEFAULT_SPEED = 20;       /*1 min is animated in 3 secs*/
    const uint MAX_SPEED = 3000;         /*1 min is animated in 20 ms*/
    const uint MIN_SPEED = 1;            /*1 min is animated in 1 min*/
    const int DEFAULT_TIME_DELAY = 20;  /*each step is done in 20 ms*/

private:
    Q_OBJECT

public:
    explicit SimulationEngine(BusinessProcessModel *processModel, SimulationData *data, QGVScene *scene, QObject *parent = nullptr);
    ~SimulationEngine();
    bool start();
    void pause();
    void stop();
    void restart();
    void setCurrentSpeed(uint currentSpeed);
    uint currentSpeed() const;
    bool isRunning();

signals:
    void started();
    void finished();
    void paused();
    void restarted();
    void eventChanged(long value);

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
    uint _currentSpeed;
    qulonglong _currentTimeMillis;
    long _lastEvent;
    QHash<QString, SmartObject*> _smartObjects;
    BusinessProcessModel *_processModel;
};

#endif // SIMULATIONENGINE_H
