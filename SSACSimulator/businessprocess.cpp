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
#include "businessprocess.h"
#include <QFile>
#include <QDebug>

BusinessProcessModel::BusinessProcessModel()
{

}

BusinessProcessModel::~BusinessProcessModel()
{
    clear();
}

int BusinessProcessModel::Load(QString filename)
{
    int errors = 0;
    clear();

    QFile file(filename);
    if(!file.open(QIODevice::ReadOnly)) {
        qInfo() << "error:" << file.errorString();
        return 1;
    }

    QTextStream in(&file);
    QStringList beginActors;
    QStringList endActors;

    //Set default values
    m_processName = "Unknown Process";
    m_thoughoutTime = 0;
    m_totalCases = 0;
    m_actors.clear();
    m_edges.clear();

    while(!in.atEnd()) {
        QString line = in.readLine();

        if(line.trimmed().isEmpty())
            continue;

        if(line.startsWith("process:")){
            QStringList fields = line.split(":");
            m_processName = fields.size() == 2 ? fields[1].trimmed() : "Unknown Process";
        } else if(line.startsWith("actors:")){
            QStringList fields = line.remove(0,7).split(",");

            for(QString str: fields){
                NodeType type = NORMAL;
                str = str.trimmed();

                if (str.startsWith("+")){
                    if(beginActors.size() == 0){
                        type = START;
                        str = str.remove(0, 1);
                        beginActors << str;
                    }else {
                        qInfo() << "Error: only one start actor is allowed";
                        errors++;
                    }
                } else if(str.startsWith("-")){
                    type = END;
                    str = str.remove(0, 1);
                    endActors << str;
                }

                Actor *actor = new Actor(str, type);
                actor->setCases(0);
                m_actors.insert(str, actor);

            }
        } else if(line.startsWith("process_througout_time:")) {
            QStringList fields = line.split(":");
            m_thoughoutTime = fields.size() == 2 ? fields[1].trimmed().toFloat(): 0.0f;
        } else if(line.startsWith("total_cases:")){
            QStringList fields = line.split(":");
            m_totalCases = fields.size() == 2 ? convertToULongLong(fields[1].trimmed()): 0;
        } else if(line.startsWith("transitions:")){
            if(beginActors.size() == 0){
                qInfo() << "Error: Any actor has been defined as the process starting point";
                errors++;
                goto exit_to_end;
            }

            if(endActors.size() == 0){
                qInfo() << "Error: Any actor has been defined as process end point";
                errors++;
                goto exit_to_end;
            }

            while(!in.atEnd()){
                QString transitions = in.readLine();

                if(transitions.trimmed().isEmpty())
                    continue;

                QStringList vt = transitions.split("=");

                if(vt.size() != 2){
                    qWarning() << "Error: processing transitions";
                    errors++;
                    continue;
                }
                QString begin = vt[0].trimmed();

                QStringList edges = vt[1].trimmed().split("!");
                QHash<QString, Edge*> hEdges;

                for(QString edge : edges){
                    QStringList values = edge.trimmed().split(";");

                    if(values.size() != 4){
                        qWarning() << "Error: processing edge:" << edge;
                        errors++;
                        continue;
                    }

                    qulonglong edge_cases = convertToULongLong( values[2].trimmed() );
                    QString end = values[0].trimmed();

                    hEdges.insert(values[0].trimmed(),
                            new Edge(begin, end,
                                     values[1].trimmed().toFloat(), edge_cases,
                                     values[3].trimmed().toInt()));

                    if(begin == beginActors[0]){
                        Actor *beginActor = m_actors[begin];
                        beginActor->setCases(beginActor->cases() + edge_cases);
                    }

                    //update node cases
                    if(m_actors.contains(end)){
                        Actor *endActor = m_actors[end];

                        if(begin != end)
                            endActor->setCases(endActor->cases() + edge_cases);
                    }else {
                        qInfo() << "Error: the actor '" << end << "' has not been defined previously";
                        errors++;
                    }
                }

                m_edges.insert(begin, hEdges);
            }
        }
    }

    if(m_actors.size() == 0){
        qInfo() << "Error: No actors has been defined";
        errors++;
    }

    if(m_edges.size() == 0){
        qInfo() << "Error: Any transition has been defined";
        errors++;
    }

    if(beginActors.size()>0){
        Actor *beginActor = m_actors[beginActors[0]];

        if(beginActor->cases() != m_totalCases){
            qInfo() << "Begin node cases mismatches the defined total cases";
            errors++;
        }
    }

exit_to_end:
    file.close();

    if(m_thoughoutTime <= 0){
        qInfo() << "Error: The thoughout time was defined as zero or was not defined";
        errors++;
    }

    if(m_totalCases <= 0){
        qInfo() << "Error: The total cases was defined as zero or was not defined";
        errors++;
    }

    if(!errors){
        m_beginActor = beginActors[0];
        m_endActors = endActors;
    }

    return errors;
}

QString BusinessProcessModel::processName() const
{
    return m_processName;
}

QHash<QString, BusinessProcessModel::Actor*> BusinessProcessModel::actors() const
{
    return m_actors;
}

QHash<QString, QHash<QString, BusinessProcessModel::Edge*> > BusinessProcessModel::edges() const
{
    return m_edges;
}

float BusinessProcessModel::thoughoutTime() const
{
    return m_thoughoutTime;
}

qulonglong BusinessProcessModel::totalCases() const
{
    return m_totalCases;
}

void BusinessProcessModel::clear()
{
    for(Actor *actor : m_actors.values())
        delete actor;

    for(QHash<QString, Edge*> edges : m_edges.values()){
        for(Edge *edge : edges.values()){
            delete edge;
        }
    }

    m_actors.clear();
    m_edges.clear();
}

QString BusinessProcessModel::beginActor() const
{
    return m_beginActor;
}

QStringList BusinessProcessModel::endActors() const
{
    return m_endActors;
}

qulonglong BusinessProcessModel::convertToULongLong(QString number)
{
    int index = number.indexOf(".");

    if(index < 0)
        return number.toULongLong();

    return number.left(index).toULongLong();
}

BusinessProcessModel::Edge::Edge(QString begin, QString end, float time, qulonglong cases, bool show)
{
    m_name = begin + "-" + end;
    m_begin = begin;
    m_end = end;
    m_time = time;
    m_cases = cases;
    m_show = show;
}

QString BusinessProcessModel::Edge::name() const
{
    return m_name;
}

QString BusinessProcessModel::Edge::begin() const
{
    return m_begin;
}

QString BusinessProcessModel::Edge::end() const
{
    return m_end;
}

float BusinessProcessModel::Edge::time() const
{
    return m_time;
}

qulonglong BusinessProcessModel::Edge::cases() const
{
    return m_cases;
}

bool BusinessProcessModel::Edge::show() const
{
    return m_show;
}

BusinessProcessModel::Actor::Actor(const QString &name, BusinessProcessModel::NodeType type)
{
    m_name = name;
    m_type = type;
    m_cases = 0;
}

QString BusinessProcessModel::Actor::name() const
{
    return m_name;
}

BusinessProcessModel::NodeType BusinessProcessModel::Actor::type() const
{
    return m_type;
}

qulonglong BusinessProcessModel::Actor::cases() const
{
    return m_cases;
}

void BusinessProcessModel::Actor::setCases(qulonglong cases)
{
    m_cases = cases;
}
