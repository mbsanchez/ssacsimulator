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
#ifndef BUSINESSPROCESS_H
#define BUSINESSPROCESS_H

#include <QObject>
#include <QHash>
#include <QList>

class QGVNode;
class QGVEdge;

class BusinessProcessModel
{

public:
    enum NodeType {NORMAL, START, END};
    class Actor{
    public:
        Actor(const QString &name, NodeType type);
        QString name() const;
        NodeType type() const;
        qulonglong cases() const;
        void setCases(qulonglong cases);
        QGVNode *gvNode() const;
        void setGvNode(QGVNode *gvNode);
        bool isFailing() const;
        void setFailure(bool isFailing);

    private:
        QString m_name;
        NodeType m_type;
        qulonglong m_cases;
        QGVNode *m_gvNode;
        bool m_failure;
    };

    class Edge{
    public:
        Edge(QString begin, QString end, float time, qulonglong cases, bool show);
        QString name() const;
        QString begin() const;
        QString end() const;
        float time() const;
        qulonglong cases() const;
        bool show() const;
        QGVEdge *gvEdge() const;
        void setGvEdge(QGVEdge *gvEdge);
        void addEventTime(double timeInMin);
        void resetTimeCount();
        double getTimeCountMean();
        double getTimeCount();
        ulong getEventsCount();


    private:
        QString m_name;
        QString m_begin;
        QString m_end;
        float m_time;
        qulonglong m_cases;
        bool m_show;
        QGVEdge *m_gvEdge;
        ulong m_eventsCount;
        double m_timeCount;
    };

public:
    BusinessProcessModel();
    ~BusinessProcessModel();
    int Load(QString filename);
    QString processName() const;
    QHash<QString, Actor*> actors() const;
    QHash<QString, QHash<QString, Edge*> > edges() const;
    float thoughoutTime() const;
    qulonglong totalCases() const;
    void clear();
    QString beginActor() const;
    QStringList endActors() const;
    int countFailingActors() const;
    QString getFailingActorsAsString() const;
    void resetFailingActors();
    void addEventTime(double timeInMin);
    void resetTimeCount();
    double getTimeCountMean() const;
    double getTimeCount() const;
    ulong getObjectsCount() const;

private:
    qulonglong convertToULongLong(QString number);

private:
    QString m_processName;
    QString m_beginActor;
    QStringList m_endActors;
    QHash<QString, Actor*> m_actors;
    QHash<QString, QHash<QString, Edge*>> m_edges;
    float m_thoughoutTime;
    qulonglong m_totalCases;
    ulong m_objectsCount;
    double m_timeCount;
};

#endif // BUSINESSPROCESS_H
