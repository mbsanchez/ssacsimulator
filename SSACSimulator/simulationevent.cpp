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
#include "simulationevent.h"

SimulationEvent::SimulationEvent(QString caseID, QString beginActor, QString endActor, float transitionTime, float startTime, QObject *parent)
    : QObject(parent),
      _caseID(caseID),
      _beginActor(beginActor),
      _endActor(endActor),
      _transitionTime(transitionTime),
      _startTime(startTime)
{

}

QString SimulationEvent::caseID() const
{
    return _caseID;
}

QString SimulationEvent::beginActor() const
{
    return _beginActor;
}

QString SimulationEvent::endActor() const
{
    return _endActor;
}

float SimulationEvent::transitionTime() const
{
    return _transitionTime;
}

float SimulationEvent::startTime() const
{
    return _startTime;
}

SimulationData::SimulationData(QObject *parent) :
    _inputFile(nullptr)
{

}

SimulationData::~SimulationData()
{
    clear();
    if(_inputFile)
        delete _inputFile;
}

SimulationEvent *SimulationData::eventAt(long i)
{
    if(i < _eventList.size())
        return _eventList.at(i);

    return nullptr;
}

int SimulationData::loadData(QString filename)
{
    _dataFilename = filename;

    //_eventList.append(new SimulationEvent("4", "BEGIN", "L0_S0", 0));
    _eventList.append(new SimulationEvent("4", "L0_S0", "L0_S1", 1, 0));
    _eventList.append(new SimulationEvent("4", "L0_S1", "L0_S2", 2, 1));
    _eventList.append(new SimulationEvent("4", "L0_S2", "L0_S5", 2, 3));
    _eventList.append(new SimulationEvent("4", "L0_S5", "L0_S6", 2, 5));
    _eventList.append(new SimulationEvent("4", "L0_S6", "L0_S8", 1, 7));
    _eventList.append(new SimulationEvent("4", "L0_S8", "L0_S10", 1, 8));
    _eventList.append(new SimulationEvent("4", "L0_S10", "L3_S29", 1, 9));
    _eventList.append(new SimulationEvent("4", "L3_S29", "L3_S30", 2, 10));
    _eventList.append(new SimulationEvent("4", "L3_S30", "L3_S31", 1, 12));
    _eventList.append(new SimulationEvent("4", "L3_S31", "L3_S33", 2, 13));
    _eventList.append(new SimulationEvent("4", "L3_S33", "L3_S34", 1, 15));
    _eventList.append(new SimulationEvent("4", "L3_S34", "L3_S35", 2, 16));
    _eventList.append(new SimulationEvent("4", "L3_S35", "L3_S37", 1, 18));
    _eventList.append(new SimulationEvent("4", "L3_S37", "END", 1, 19));

    return 0;
}

void SimulationData::clear()
{
    qDeleteAll(_eventList);
    _eventList.clear();
}

void SimulationData::restart()
{
    //TODO: reload the data from the beginning
}

long SimulationData::eventsCount()
{
    return _eventList.size();
}

int SimulationData::getNextChunck(int chunkLength)
{
    return 0;
}
