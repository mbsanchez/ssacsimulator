#ifndef QGVEDGEPRIVATE_H
#define QGVEDGEPRIVATE_H

#include <cgraph.h>

class QGVNode;
class QGVEdgePrivate
{
	public:
        QGVEdgePrivate(Agedge_t *edge, QGVNode *source = nullptr, QGVNode *target=nullptr);

		void setEdge(Agedge_t *edge);
		Agedge_t* edge() const;
        QGVNode *source() const;
        QGVNode *target() const;

private:
        Agedge_t* _edge;
        QGVNode *_source;
        QGVNode *_target;

};

#endif // QGVEDGEPRIVATE_H
