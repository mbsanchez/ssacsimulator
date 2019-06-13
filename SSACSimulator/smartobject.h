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
#ifndef SMARTOBJECT_H
#define SMARTOBJECT_H

#include <QObject>
#include <QGraphicsItem>
#include <QGraphicsItemAnimation>

class QGVEdge;

class SmartObject : public QGraphicsItem
{
    class SegmentData{
    public:
        SegmentData() : lenght(0), percent(0) {}
        SegmentData(qreal lenght, qreal percent){
            this->lenght = lenght;
            this->percent = percent;
        }
    public:
        qreal lenght;
        qreal percent;
    };

public:
    SmartObject(QString objectID, QGraphicsItem *parent = nullptr);
    void paint(QPainter * painter, const QStyleOptionGraphicsItem * option, QWidget * widget = nullptr);
    QRectF boundingRect() const;
    QString objectID() const;
    void setPathEdge(QGVEdge *pathEdge, qreal animationTimeInMin);
    void nextAnimationStep(long dxMillis);
    bool isAnimationFinished();
    QString endActor() const;
    void setEndActor(const QString &value);

private:
    void finished();
    void started();
    void centerInCurrentFrame();
    void centerInPoint(QPointF point);
    void prepareSlerpData();
    QPointF centerPoint();

private:
    QString _objectID;
    QString _endActor;
    QGVEdge *_pathEdge;
    long _currentTime;
    long _currentSegment;
    long _animationTimeMillis;
    QVector<SegmentData> _slerpData;
    qreal _totalLenght;
};

#endif // SMARTOBJECT_H
