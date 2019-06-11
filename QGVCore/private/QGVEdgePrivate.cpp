#include "QGVEdgePrivate.h"
#include "QGVNode.h"

QGVEdgePrivate::QGVEdgePrivate(Agedge_t *edge, QGVNode *source, QGVNode *target)
{
	setEdge(edge);
    _source = source;
    _target = target;
}

void QGVEdgePrivate::setEdge(Agedge_t *edge)
{
	_edge = edge;
}

Agedge_t* QGVEdgePrivate::edge() const
{
	return _edge;
}

QGVNode *QGVEdgePrivate::source() const
{
    return _source;
}

QGVNode *QGVEdgePrivate::target() const
{
    return _target;
}
