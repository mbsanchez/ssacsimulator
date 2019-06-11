/***************************************************************
QGVCore Sample
Copyright (c) 2014, Bergont Nicolas, All rights reserved.

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
#include "MainWindow.h"
#include "moc_MainWindow.cpp"
#include "ui_MainWindow.h"
#include "QGVScene.h"
#include "QGVNode.h"
#include "QGVEdge.h"
#include "QGVSubGraph.h"
#include <QMessageBox>
#include "businessprocess.h"
#include <QtDebug>

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow),
    currentBpm(new BusinessProcessModel())
{
    ui->setupUi(this);

    _scene = new QGVScene("DEMO", this);
    ui->graphicsView->setScene(_scene);

    connect(_scene, SIGNAL(nodeContextMenu(QGVNode*)), SLOT(nodeContextMenu(QGVNode*)));
    connect(_scene, SIGNAL(nodeDoubleClick(QGVNode*)), SLOT(nodeDoubleClick(QGVNode*)));
    connect(_scene, SIGNAL(edgeDoubleClick(QGVEdge*)), SLOT(edgeDoubleClick(QGVEdge*)));
}

MainWindow::~MainWindow()
{
    delete ui;
    delete currentBpm;
}

void MainWindow::drawGraph()
{
    currentBpm->Load("D:\\Users\\mbsanchez\\Documents\\Academia\\ULA\\Doctorado\\DataSets I4.0\\process graph.p");

    //Configure scene attributes
    _scene->setGraphAttribute("label", currentBpm->processName());

    _scene->setGraphAttribute("splines", "true");
    _scene->setGraphAttribute("rankdir", "LR");
    //_scene->setGraphAttribute("concentrate", "true"); //Error !
    _scene->setGraphAttribute("dpi", "96.0");
    _scene->setGraphAttribute("pad", "0.2");
    _scene->setGraphAttribute("nodesep", "0.4");

    _scene->setNodeAttribute("shape", "box");
    _scene->setNodeAttribute("overlap", "prism");
    _scene->setNodeAttribute("style", "filled");
    _scene->setNodeAttribute("fillcolor", "white");
    //_scene->setNodeAttribute("height", "1.2");
    _scene->setEdgeAttribute("minlen", "2");
    //_scene->setEdgeAttribute("dir", "both");

    QHash<QString, QGVNode*> nodes;

    for(BusinessProcessModel::Actor *actor : currentBpm->actors().values()){
        QGVNode *node = _scene->addNode(actor->name());
        node->setAttribute("xlabel", QString::number(actor->cases()));
        nodes.insert(actor->name(), node);
    }

    //Add edges
    auto edges = currentBpm->edges();
    for(BusinessProcessModel::Actor *actor : currentBpm->actors().values()){
        auto actor_edges = edges[actor->name()];

        for(BusinessProcessModel::Edge *edge : actor_edges.values() ){
            if(!edge->show())
                continue;

            _scene->addEdge(nodes[edge->begin()], nodes[edge->end()], QString::number((double)edge->time()));
            /*_scene->addEdge(node1, node2, "TTL")->setAttribute("color", "red");*/
        }
    }

    //Layout scene
    _scene->applyLayout();

    //Fit in view
    ui->graphicsView->fitInView(_scene->sceneRect(), Qt::KeepAspectRatio);
}

void MainWindow::nodeContextMenu(QGVNode *node)
{
    //Context menu exemple
    QMenu menu(node->label());

    menu.addSeparator();
    menu.addAction(tr("Informations"));
    menu.addAction(tr("Options"));

    QAction *action = menu.exec(QCursor::pos());
    if(action == nullptr)
        return;
}

void MainWindow::nodeDoubleClick(QGVNode *node)
{
    BusinessProcessModel::Actor *actor = currentBpm->actors()[node->label()];
    QMessageBox::information(this, tr("Actor %1 Info").arg(node->label()), tr("Cases %1").arg(QString::number(actor->cases())));
}

void MainWindow::edgeDoubleClick(QGVEdge *edge)
{
    QGVNode *source = edge->getSource();
    QGVNode *target = edge->getTarget();

    if(!source || !target){
        qInfo() << "Invalid edge, source or target is null";
        return;
    }

    QString slabel = source->label();
    QString tlabel = target->label();

    BusinessProcessModel::Edge *tedge = currentBpm->edges()[slabel][tlabel];

    QMessageBox::information(this, tr("Edge %1 Info").arg(tedge->name()), tr("Cases %1, Avg Time %2").arg(QString::number(tedge->cases()), QString::number((double)tedge->time())));
}
