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
#include "MainWindow.h"
#include "moc_MainWindow.cpp"
#include "ui_MainWindow.h"
#include "QGVScene.h"
#include "QGVNode.h"
#include "QGVEdge.h"
#include "QGVSubGraph.h"
#include <QMessageBox>
#include "businessprocess.h"
#include "smartobject.h"
#include "simulationengine.h"
#include "simulationevent.h"
#include <QtDebug>
#include <QFileDialog>

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow),
    _scene(nullptr),
    currentBpm(new BusinessProcessModel()),
    _simEngine(nullptr),
    _simData(nullptr)
{
    ui->setupUi(this);
    _simData = new SimulationData();
    _simData->loadData("");

    createNewScene();
    EnableButtons(INITIAL_CONFIG);
}

MainWindow::~MainWindow()
{
    delete ui;
    delete currentBpm;

    if(_simData)
        delete _simData;

    if(_simEngine){
        if(_simEngine->isRunning())
            _simEngine->stop();

        delete _simEngine;
    }
}

void MainWindow::drawGraph(QString filename)
{
    qInfo() << "Loading file: " << filename;
    int errors = currentBpm->Load(filename);

    if(errors){
        QMessageBox::information(this, APP_NAME, "We've found errors loading the process model, check the log file for details");

        return;
    }

    qInfo() << "Process file was loaded without errors";

    //Create New Scene
    createNewScene();

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
        actor->setGvNode(node);
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

            QGVEdge *gvEdge = _scene->addEdge(nodes[edge->begin()], nodes[edge->end()], QString::number((double)edge->time()));
            edge->setGvEdge(gvEdge);
            /*_scene->addEdge(node1, node2, "TTL")->setAttribute("color", "red");*/
        }
    }

    //Layout scene
    _scene->applyLayout();

    //Fit in view
    ui->graphicsView->items().clear();
    ui->graphicsView->fitInView(_scene->sceneRect(), Qt::KeepAspectRatio);
    EnableButtons(MODEL_OPENED);
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

void MainWindow::exitClicked()
{
    if(QMessageBox::question( this, APP_NAME, "Do you want to close?") == QMessageBox::Yes){
        qApp->exit(0);
    }
}

void MainWindow::openClicked()
{
    QString filename =  QFileDialog::getOpenFileName(
              this,
              "Open Business Process Model",
              QDir::currentPath(),
              "All files (*.*) ;; BP files (*.p)");

    if( !filename.isNull() )
    {
        drawGraph(filename);
    }
}

void MainWindow::openTestDataClicked()
{
    EnableButtons(DATA_OPENED);
    if(_simEngine){
        if(_simEngine->isRunning())
            _simEngine->stop();

        delete _simEngine;
    }
    _simEngine = new SimulationEngine(currentBpm, _simData, _scene);
    connect(_simEngine, &SimulationEngine::started, [this](){
        EnableButtons(SIM_STARTED);
    });
    connect(_simEngine, &SimulationEngine::finished, [this](){
        EnableButtons(SIM_STOPPED);
    });
    connect(_simEngine, &SimulationEngine::paused, [this](){
        EnableButtons(SIM_PAUSED);
    });
    connect(_simEngine, &SimulationEngine::restarted, [this](){
        EnableButtons(SIM_RESTARTED);
    });
}

void MainWindow::startSimulationClicked()
{

    if(_simEngine == nullptr){
        qCritical() << "Error the simulation engine is not ready";
        return;
    }

    EnableButtons(SIM_STARTED);
    _simEngine->start();
}

void MainWindow::stopSimulationClicked()
{

    if(_simEngine == nullptr){
        qCritical() << "Error the simulation engine is not ready";
        return;
    }

    EnableButtons(SIM_STOPPED);
    _simEngine->stop();
}

void MainWindow::pauseSimulationClicked()
{
    if(_simEngine == nullptr){
        qCritical() << "Error the simulation engine is not ready";
        return;
    }

    EnableButtons(SIM_PAUSED);
    _simEngine->pause();
}

void MainWindow::restartSimulationClicked()
{
    if(_simEngine == nullptr){
        qCritical() << "Error the simulation engine is not ready";
        return;
    }

    EnableButtons(SIM_RESTARTED);
    _simEngine->restart();
}

void MainWindow::closeEvent(QCloseEvent *event)
{
    if(QMessageBox::question( this, APP_NAME, "Do you want to close?") == QMessageBox::Yes){
        qApp->exit(0);
    } else {
        event->ignore();
    }
}

void MainWindow::createNewScene()
{
    if(_scene){
        _scene->clear();
        delete _scene;
    }
    _scene = new QGVScene("DEMO", this);
    ui->graphicsView->setScene(_scene);

    connect(_scene, SIGNAL(nodeContextMenu(QGVNode*)), SLOT(nodeContextMenu(QGVNode*)));
    connect(_scene, SIGNAL(nodeDoubleClick(QGVNode*)), SLOT(nodeDoubleClick(QGVNode*)));
    connect(_scene, SIGNAL(edgeDoubleClick(QGVEdge*)), SLOT(edgeDoubleClick(QGVEdge*)));
}

void MainWindow::EnableButtons(MainWindow::AppAction action)
{
    switch(action){
    case INITIAL_CONFIG:
        ui->openAction->setEnabled(true);
        ui->openTestDataAction->setEnabled(false);
        ui->startAction->setEnabled(false);
        ui->stopAction->setEnabled(false);
        ui->pauseAction->setEnabled(false);
        ui->restartAction->setEnabled(false);
        break;
    case MODEL_OPENED:
        ui->openTestDataAction->setEnabled(true);
        ui->startAction->setEnabled(false);
        ui->stopAction->setEnabled(false);
        ui->pauseAction->setEnabled(false);
        ui->restartAction->setEnabled(false);
        break;
    case DATA_OPENED:
        ui->startAction->setEnabled(true);
        ui->stopAction->setEnabled(false);
        ui->pauseAction->setEnabled(false);
        ui->restartAction->setEnabled(false);
        break;
    case SIM_STARTED:
    case SIM_RESTARTED:
        ui->openAction->setEnabled(false);
        ui->openTestDataAction->setEnabled(false);
        ui->startAction->setEnabled(false);
        ui->stopAction->setEnabled(true);
        ui->pauseAction->setEnabled(true);
        ui->restartAction->setEnabled(false);
        break;
    case SIM_STOPPED:
        ui->openAction->setEnabled(true);
        ui->openTestDataAction->setEnabled(true);
        ui->startAction->setEnabled(true);
        ui->stopAction->setEnabled(false);
        ui->pauseAction->setEnabled(false);
        ui->restartAction->setEnabled(false);
        break;
    case SIM_PAUSED:
        ui->openAction->setEnabled(true);
        ui->openTestDataAction->setEnabled(true);
        ui->startAction->setEnabled(true);
        ui->stopAction->setEnabled(true);
        ui->pauseAction->setEnabled(false);
        ui->restartAction->setEnabled(true);
        break;
    }
}

