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
#include <QtDebug>

SimulationEvent::SimulationEvent(QString caseID, QString beginActor, QString endActor, double transitionTime, double startTime, QObject *parent)
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

double SimulationEvent::transitionTime() const
{
    return _transitionTime;
}

double SimulationEvent::startTime() const
{
    return _startTime;
}

ulong SimulationEvent::transitionTimeInMs() const
{
    return static_cast<ulong>(_transitionTime * 60ul * 1000ul);
}

qulonglong SimulationEvent::startTimeInMs() const
{
    return static_cast<qulonglong>(_startTime * 60ull * 1000ull);
}

SimulationData::SimulationData(QObject *parent) :
    QObject (parent),
    _inputFile(nullptr),
    _lastAccessedIndex(-1),
    _events(0),
    _minTime(0),
    _maxTime(0)
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
    if(i < _eventList.size()){
        _lastAccessedIndex = i;
        return _eventList.at(i);
    }

    return nullptr;
}

int SimulationData::loadData(QString filename)
{
    _dataFilename = filename;

    if(!_inputFile)
        _inputFile = new std::ifstream();

    if(_inputFile->is_open())
        _inputFile->close();

    clear();
    _inputFile->open(filename.toLocal8Bit().data());

    if(_inputFile->fail()){
        qInfo() << QString("Error opening the file %1").arg(filename);
        return 1;
    }

    _lastAccessedIndex = -1;
    if(readHeader()!=0){
        qInfo() << "Error reading header";
        return 1;
    }

    return getNextChunck(DATA_INITIAL_CHUNK_LENGHT);
}

void SimulationData::createTestData1()
{
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
    _eventList.append(new SimulationEvent("9", "L3_S37", "END", 0, 106));

    _eventList.append(new SimulationEvent("10", "L1_S24", "L2_S27", 0, 106));
    _eventList.append(new SimulationEvent("10", "L2_S27", "L3_S29", 0, 106));
    _eventList.append(new SimulationEvent("10", "L3_S29", "L3_S30", 0, 106));
    _eventList.append(new SimulationEvent("10", "L3_S30", "L3_S32", 0, 106));
    _eventList.append(new SimulationEvent("10", "L3_S32", "L3_S33", 0, 106));
    _eventList.append(new SimulationEvent("10", "L3_S33", "L3_S34", 0, 106));
    _eventList.append(new SimulationEvent("10", "L3_S34", "L3_S35", 1, 106));
    _eventList.append(new SimulationEvent("11", "L1_S25", "L1_S25", 0, 106));
    _eventList.append(new SimulationEvent("11", "L1_S25", "L1_S25", 0, 106));
    _eventList.append(new SimulationEvent("11", "L1_S25", "L2_S26", 0, 106));
    _eventList.append(new SimulationEvent("11", "L2_S26", "L3_S29", 0, 106));
    _eventList.append(new SimulationEvent("11", "L3_S29", "L3_S30", 0, 106));
    _eventList.append(new SimulationEvent("11", "L3_S30", "L3_S31", 0, 106));
    _eventList.append(new SimulationEvent("11", "L3_S31", "L3_S33", 0, 106));
    _eventList.append(new SimulationEvent("11", "L3_S33", "L3_S34", 0, 106));
    _eventList.append(new SimulationEvent("11", "L3_S34", "L3_S36", 2, 106));
    _eventList.append(new SimulationEvent("14", "L1_S24", "L2_S27", 1, 106));
    _eventList.append(new SimulationEvent("10", "L3_S35", "L3_S37", 1, 107));
    _eventList.append(new SimulationEvent("14", "L2_S27", "L3_S29", 4, 107));
    _eventList.append(new SimulationEvent("10", "L3_S37", "END", 1, 108));
    _eventList.append(new SimulationEvent("11", "L3_S36", "L3_S37", 1, 108));
    _eventList.append(new SimulationEvent("11", "L3_S37", "L3_S38", 2, 109));
    _eventList.append(new SimulationEvent("11", "L3_S38", "END", 1, 110));
    _eventList.append(new SimulationEvent("14", "L3_S29", "L3_S30", 1, 111));
    _eventList.append(new SimulationEvent("14", "L3_S30", "L3_S32", 2, 112));
    _eventList.append(new SimulationEvent("14", "L3_S32", "L3_S33", 3, 114));
    _eventList.append(new SimulationEvent("14", "L3_S33", "L3_S34", 1, 117));
    _eventList.append(new SimulationEvent("14", "L3_S34", "L3_S35", 2, 118));
    _eventList.append(new SimulationEvent("14", "L3_S35", "L3_S37", 1, 120));
    _eventList.append(new SimulationEvent("14", "L3_S37", "END", 1, 121));

    _eventList.append(new SimulationEvent("13", "L3_S35", "L3_S36", 2, 122));
    _eventList.append(new SimulationEvent("13", "L3_S36", "L3_S37", 1, 124));
    _eventList.append(new SimulationEvent("13", "L3_S37", "END", 0, 125));
}

void SimulationData::clear()
{
    qDeleteAll(_eventList);
    _eventList.clear();
    _minTime = 0;
    _maxTime = 0;
    _events = 0;
}

void SimulationData::restart()
{
    //TODO: xxxxxxx, crashed
    _lastAccessedIndex = -1;
    //loadData(_dataFilename);
}

long SimulationData::eventsCount()
{
    return _eventList.size();
}

int SimulationData::getNextChunck(int chunkLength)
{
    if(!_inputFile)
        return 1;

    char line[1024];

    for (long i=0; i < chunkLength && !_inputFile->eof(); i++) {
        _inputFile->getline(line, 1024,'\n');

        QStringList row = QString::fromLocal8Bit(line).split(",");

        if(row.isEmpty())
            continue;

        if(row.size() != 5){
            qCritical() << QString("row %1, invalid format").arg(QString::number(i));
            continue;
        }

        bool durationOk=false, startTimeOk=false;
        double duration = row[3].trimmed().toDouble(&durationOk);
        double startTime = row[4].trimmed().toDouble(&startTimeOk);

        if(!durationOk && !startTimeOk){
            continue;
        }

        _eventList.append(new SimulationEvent(row[0], row[1], row[2], duration, startTime));
    }

    qInfo() << "Events data chunk loaded";
    return 0;
}

int SimulationData::readHeader()
{
    char line[1024];

    //Skip the header
    _inputFile->getline(line, 1024,'\n');

    if(_inputFile->fail()){
        qCritical() << "Error reading the events data file";
        return 1;
    }

    _inputFile->getline(line, 1024,'\n');

    if(_inputFile->fail()){
        qCritical() << "Error reading the events data file";
        return 1;
    }

    QStringList row = QString::fromLocal8Bit(line).split(",");
    if(row.size() != 5) {
        qCritical() << "Error events data must contains 5 columns";
        return 1;
    }

    bool ok = false;

    _events = row[0].trimmed().toULong(&ok);

    if(!ok || _events <= 0){
        qCritical() << "Error reading events number, it mus be a number >= 0";
        return 1;
    }

    _minTime = row[1].trimmed().toDouble(&ok);
    if(!ok || _minTime < 0){
        qCritical() << "Error reading min simulation time, it mus be a number >= 0";
        return 1;
    }

    _maxTime = row[2].trimmed().toDouble(&ok);
    if(!ok || _maxTime <= 0){
        qCritical() << "Error reading max simulation time, it mus be a number > 0";
        return 1;
    }

    qDebug() << QString("events: %1, min time: %2, max time: %3").arg(QString::number(_events),
                                                                      QString::number(_minTime),
                                                                      QString::number(_maxTime));

    return 0;
}

qreal SimulationData::maxTime() const
{
    return _maxTime;
}

qreal SimulationData::minTime() const
{
    return _minTime;
}

ulong SimulationData::events() const
{
    return _events;
}
