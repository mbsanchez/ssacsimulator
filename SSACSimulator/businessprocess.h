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

    private:
        QString m_name;
        NodeType m_type;
        qulonglong m_cases;
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

    private:
        QString m_name;
        QString m_begin;
        QString m_end;
        float m_time;
        qulonglong m_cases;
        bool m_show;
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
};

#endif // BUSINESSPROCESS_H
