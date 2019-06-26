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
#include "smartobject.h"
#include <QPainter>
#include <QWidget>
#include <QGVEdge.h>

SmartObject::SmartObject(QString objectID, QGraphicsItem *parent) : QGraphicsItem (parent),
    _objectID(objectID),
    _pathEdge(nullptr),
    _currentTime(0),
    _currentSegment(0),
    _animationTimeMillis(0),
    _totalLenght(0),
    _timeCount(0)
{
    setFlag(QGraphicsItem::ItemIsSelectable, false);
}

void SmartObject::paint(QPainter *painter, const QStyleOptionGraphicsItem *option, QWidget *widget)
{
    Q_UNUSED(option)
    Q_UNUSED(widget)

    QRectF rect = boundingRect();

    painter->save();

    painter->setPen(Qt::black);
    painter->drawEllipse(rect);
    painter->setPen(Qt::red);
    painter->setBrush(Qt::red);
    rect.adjust(1,1,-1,-1);
    painter->drawEllipse(rect);

    painter->restore();
}

QRectF SmartObject::boundingRect() const
{
    return QRectF(0,0,15,15);
}

QString SmartObject::objectID() const
{
    return _objectID;
}

void SmartObject::setPathEdge(QGVEdge *pathEdge, ulong animationTimeInMs)
{
    _pathEdge = pathEdge;
    _currentSegment = 0;
    _currentTime = 0;
    _animationTimeMillis = animationTimeInMs;
    _timeCount += animationTimeInMs / 60000.0;

    if(_animationTimeMillis <= 0 || _pathEdge == nullptr){
        _animationTimeMillis = 0;
        finished();
    } else {
        prepareSlerpData();
        started();
    }
}

void SmartObject::nextAnimationStep(ulong dxMillis)
{
    if(_pathEdge == nullptr || _currentTime >= _animationTimeMillis || dxMillis == 0){
        return;
    }

    ulong x = _currentTime + dxMillis;

    if(x >= _animationTimeMillis)
        x = _animationTimeMillis;

    int i = 0, segment = -1;
    qreal xTime = 0;

    for(SegmentData data : _slerpData){
        xTime += data.percent * _animationTimeMillis;

        if(x < xTime){
           segment = i;
           break;
        }
        i++;
    }

    _currentTime = x;
    if(segment == -1 || segment == _pathEdge->getPath().elementCount()){
        finished();
    } else {
        _currentSegment = segment;

        QPointF a = _pathEdge->getPath().elementAt(_currentSegment);
        QPointF b = _pathEdge->getPath().elementAt(_currentSegment + 1);

        long animationSteps = static_cast<long>(_slerpData.at(_currentSegment).percent * _animationTimeMillis / static_cast<qreal>(dxMillis));

        if(animationSteps == 0){
            _currentSegment++;
            centerInCurrentFrame();
            return;
        }

        qreal px = pos().x() + centerPoint().x() + (b.x() - a.x()) / animationSteps;
        qreal py = a.y() + (b.y() - a.y()) * ((px - a.x())/(b.x() - a.x()));

        centerInPoint(QPointF(px, py));
    }
}

bool SmartObject::isAnimationFinished()
{
    return _currentTime >= _animationTimeMillis;
}

void SmartObject::finished()
{
    hide();
}

void SmartObject::started()
{
    centerInCurrentFrame();
    show();
}

void SmartObject::centerInCurrentFrame()
{
    centerInPoint(_pathEdge->getPath().elementAt(_currentSegment));
}

void SmartObject::centerInPoint(QPointF point)
{
    QPointF newPos = point - centerPoint();
    setPos(newPos);
}

void SmartObject::prepareSlerpData()
{
    QPainterPath path;
    _slerpData.clear();
    _totalLenght = 0;

    if(_pathEdge == nullptr || (path = _pathEdge->getPath()).elementCount() <= 1)
        return;

    QVector<qreal> sdata;
    for(int i = 0; i < path.elementCount() - 1; i++){
        QPointF a = path.elementAt(i), b = path.elementAt(i+1);
        qreal lenght = QLineF(a, b).length();
        _totalLenght += lenght;
        sdata.append(lenght);
    }

    if(_totalLenght < std::numeric_limits<double>::epsilon())
        return;


    for(qreal lenght : sdata){
        _slerpData.append(SegmentData(lenght, lenght / _totalLenght));
    }
}

QPointF SmartObject::centerPoint()
{
    QRectF rect = boundingRect();

    return QPointF(rect.width() / 2, rect.height() / 2);
}

qreal SmartObject::timeCount() const
{
    return _timeCount;
}

QString SmartObject::endActor() const
{
    return _endActor;
}

void SmartObject::setEndActor(const QString &value)
{
    _endActor = value;
}
