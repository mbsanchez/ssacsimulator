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

    _eventList.append(new SimulationEvent("5", "L0_S12", "L0_S13", 1, 20));
    _eventList.append(new SimulationEvent("5", "L0_S13", "L0_S15", 2, 21));
    _eventList.append(new SimulationEvent("5", "L0_S15", "L0_S16", 2, 23));
    _eventList.append(new SimulationEvent("5", "L0_S16", "L0_S19", 1, 25));
    _eventList.append(new SimulationEvent("5", "L0_S19", "L0_S20", 0, 26));
    _eventList.append(new SimulationEvent("5", "L0_S20", "L0_S23", 1, 26));
    _eventList.append(new SimulationEvent("5", "L0_S23", "L3_S39", 2, 27));
    _eventList.append(new SimulationEvent("5", "L3_S39", "L3_S40", 1, 29));
    _eventList.append(new SimulationEvent("5", "L3_S40", "L3_S41", 3, 30));
    _eventList.append(new SimulationEvent("5", "L3_S41", "L3_S44", 2, 33));
    _eventList.append(new SimulationEvent("5", "L3_S44", "L3_S45", 1, 35));
    _eventList.append(new SimulationEvent("5", "L3_S45", "L3_S47", 2, 36));
    _eventList.append(new SimulationEvent("5", "L3_S47", "L3_S48", 1, 38));
    _eventList.append(new SimulationEvent("5", "L3_S48", "L3_S50", 2, 39));
    _eventList.append(new SimulationEvent("5", "L3_S50", "L3_S51", 1, 41));
    _eventList.append(new SimulationEvent("5", "L3_S51", "END", 0, 42));

    _eventList.append(new SimulationEvent("6", "L0_S12", "L0_S13", 1, 42));
    _eventList.append(new SimulationEvent("6", "L0_S13", "L0_S14", 2, 43));
    _eventList.append(new SimulationEvent("6", "L0_S14", "L0_S17", 2, 45));
    _eventList.append(new SimulationEvent("6", "L0_S17", "L0_S18", 3, 47));
    _eventList.append(new SimulationEvent("6", "L0_S18", "L0_S20", 2, 50));
    _eventList.append(new SimulationEvent("6", "L0_S20", "L0_S21", 2, 52));
    _eventList.append(new SimulationEvent("6", "L0_S21", "L3_S40", 2, 54));
    _eventList.append(new SimulationEvent("6", "L3_S40", "L3_S41", 1, 56));
    _eventList.append(new SimulationEvent("6", "L3_S41", "L3_S45", 2, 57));
    _eventList.append(new SimulationEvent("6", "L3_S45", "L3_S46", 3, 59));
    _eventList.append(new SimulationEvent("6", "L3_S46", "L3_S47", 2, 62));
    _eventList.append(new SimulationEvent("6", "L3_S47", "L3_S50", 1, 64));
    _eventList.append(new SimulationEvent("6", "L3_S50", "END", 1, 65));

    _eventList.append(new SimulationEvent("7", "L1_S25", "L1_S25", 1, 66));
    _eventList.append(new SimulationEvent("7", "L1_S25", "L1_S25", 2, 67));
    _eventList.append(new SimulationEvent("7", "L1_S25", "L2_S26", 1, 69));
    _eventList.append(new SimulationEvent("7", "L2_S26", "L3_S29", 4, 70));
    _eventList.append(new SimulationEvent("7", "L3_S29", "L3_S30", 1, 74));
    _eventList.append(new SimulationEvent("7", "L3_S30", "L3_S31", 2, 75));
    _eventList.append(new SimulationEvent("7", "L3_S31", "L3_S33", 1, 77));
    _eventList.append(new SimulationEvent("7", "L3_S33", "L3_S34", 3, 78));
    _eventList.append(new SimulationEvent("7", "L3_S34", "L3_S36", 2, 81));
    _eventList.append(new SimulationEvent("7", "L3_S36", "L3_S37", 1, 83));
    _eventList.append(new SimulationEvent("7", "L3_S37", "L3_S38", 2, 84));
    _eventList.append(new SimulationEvent("7", "L3_S38", "END", 1, 86));

    _eventList.append(new SimulationEvent("8", "L1_S24", "L2_S27", 1, 87));
    _eventList.append(new SimulationEvent("8", "L2_S27", "L3_S29", 4, 88));
    _eventList.append(new SimulationEvent("8", "L3_S29", "L3_S30", 1, 92));
    _eventList.append(new SimulationEvent("8", "L3_S30", "L3_S32", 2, 93));
    _eventList.append(new SimulationEvent("8", "L3_S32", "L3_S33", 3, 95));
    _eventList.append(new SimulationEvent("8", "L3_S33", "L3_S34", 1, 98));
    _eventList.append(new SimulationEvent("8", "L3_S34", "L3_S35", 2, 99));
    _eventList.append(new SimulationEvent("8", "L3_S35", "L3_S37", 1, 101));
    _eventList.append(new SimulationEvent("8", "L3_S37", "END", 1, 102));

    _eventList.append(new SimulationEvent("9", "L3_S35", "L3_S36", 2, 103));
    _eventList.append(new SimulationEvent("9", "L3_S36", "L3_S37", 1, 105));

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
