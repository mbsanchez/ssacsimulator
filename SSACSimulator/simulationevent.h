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
    const static long DATA_CHUNK_LENGHT = 1000;
    Q_OBJECT
public:
    explicit SimulationEvent(QString caseID, QString beginActor, QString endActor, float transitionTime, float startTime, QObject *parent = nullptr);
    QString caseID() const;
    QString beginActor() const;
    QString endActor() const;
    float transitionTime() const;
    float startTime() const;

private:
    QString _caseID;
    QString _beginActor;
    QString _endActor;
    float _transitionTime;
    float _startTime;
};

class SimulationData : public QObject {
    Q_OBJECT
public:
    SimulationData(QObject *parent = nullptr);
    ~SimulationData();
    SimulationEvent *eventAt(long i);
    int loadData(QString filename);
    void clear();
    void restart();
    long eventsCount();
private:
    int getNextChunck(int chunkLength);

private:
    std::ifstream *_inputFile;
    QString _dataFilename;
    QVector<SimulationEvent*> _eventList;
};

#endif // SIMULATIONEVENT_H
