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
#ifndef SIMULATIONEVENT_H
#define SIMULATIONEVENT_H

#include <QObject>
#include <QVector>
#include <fstream>

class SimulationEvent : public QObject
{  
    Q_OBJECT
public:
    explicit SimulationEvent(QString caseID, QString beginActor, QString endActor, double transitionTime, double startTime, int fails = -1, QObject *parent = nullptr);
    QString caseID() const;
    QString beginActor() const;
    QString endActor() const;
    double transitionTime() const;
    double startTime() const;
    ulong transitionTimeInMs() const;
    qulonglong startTimeInMs() const;
    int fails() const;

private:
    QString _caseID;
    QString _beginActor;
    QString _endActor;
    double _transitionTime;
    double _startTime;
    int _fails;
};

class SimulationData : public QObject {
    const static long DATA_INITIAL_CHUNK_LENGHT = 100000;
    const static long DATA_SMALL_CHUNK_LENGHT = 10000;
    Q_OBJECT
public:
    SimulationData(QObject *parent = nullptr);
    ~SimulationData();
    SimulationEvent *eventAt(long i);
    int loadData(QString filename);
    void createTestData1();
    void clear();
    void restart();
    long eventsCount();
    ulong events() const;
    qreal minTime() const;
    qreal maxTime() const;

private:
    int getNextChunck(int chunkLength);
    int readHeader();

private:
    std::ifstream *_inputFile;
    QString _dataFilename;
    QVector<SimulationEvent*> _eventList;
    long _lastAccessedIndex;
    ulong _events;
    qreal _minTime;
    qreal _maxTime;
};

#endif // SIMULATIONEVENT_H
