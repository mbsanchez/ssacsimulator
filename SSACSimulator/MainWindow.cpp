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
#include <QSlider>
#include <QSettings>
#include <QStandardPaths>

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow),
    _scene(nullptr),
    currentBpm(new BusinessProcessModel()),
    _simEngine(nullptr),
    _simData(nullptr)
{

    QCoreApplication::setOrganizationName("Personal");
    QCoreApplication::setApplicationName(APP_NAME);

    ui->setupUi(this);
    _simData = new SimulationData();

    createNewScene();
    EnableButtons(INITIAL_CONFIG);

    ui->speedSlider->setValue(200);
    ui->mainToolBar->insertWidget( nullptr, ui->speedSlider);
    ui->mainToolBar->addSeparator();
    connect(ui->speedSlider, SIGNAL(valueChanged(int)), this, SLOT(speedChanged(int)));
}

MainWindow::~MainWindow()
{
    delete ui;
    delete currentBpm;

    if(_simData)
        delete _simData;

    if(_simEngine){
        _simEngine->disconnect();
        if(_simEngine->isRunning()) {
            _simEngine->stop();
        }

        delete _simEngine;
    }

    if(_scene) {
        _scene->disconnect();
        delete _scene;
    }
}

void MainWindow::drawGraph(QString filename)
{
    qInfo() << "Loading file: " << filename;
    int errors = currentBpm->Load(filename);

    if(errors){
        showDashboarMessage(ERROR, tr("We've found errors loading the process model, check the log file for details."));
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

            QGVEdge *gvEdge = _scene->addEdge(nodes[edge->begin()], nodes[edge->end()], QString::number(static_cast<double>(edge->time())));
            edge->setGvEdge(gvEdge);
            /*_scene->addEdge(node1, node2, "TTL")->setAttribute("color", "red");*/
        }
    }

    //Layout scene
    _scene->applyLayout();

    //Fit in view
    ui->graphicsView->items().clear();
    ui->graphicsView->fitInView(_scene->sceneRect(), Qt::KeepAspectRatio);
    showDashboarMessage(INFO, tr("Process Model %1 loaded without issues.").arg(currentBpm->processName()));
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

    QMessageBox::information(this, tr("Edge %1 Info").arg(tedge->name()), tr("Cases %1, Avg Time %2").arg(QString::number(tedge->cases()), QString::number(static_cast<double>(tedge->time()))));
}

void MainWindow::exitClicked()
{
    if(QMessageBox::question( this, APP_NAME, "Do you want to close?") == QMessageBox::Yes){
        qApp->exit(0);
    }
}

void MainWindow::openClicked()
{
    QSettings settings;
    QString lastFolder = settings.value("lastFolder", "").toString();

    QString filename =  QFileDialog::getOpenFileName(
              this,
              "Open Business Process Model",
              lastFolder.isEmpty() ? QStandardPaths::
                                     standardLocations(QStandardPaths::
                                                       DocumentsLocation).
                                     at(0) : lastFolder,
              "BP files (*.pg);;All files (*.*)");

    if( !filename.isNull() )
    {
        settings.setValue("lastFolder", QFileInfo(filename).absolutePath());
        drawGraph(filename);
    }
}

void MainWindow::openTestDataClicked()
{
    QSettings settings;
    QString lastFolder = settings.value("lastFolder", "").toString();

    if(_simEngine && _simEngine->isRunning())
        _simEngine->pause();

    //_simData->createTestData1();

    QString filename =  QFileDialog::getOpenFileName(
              this,
              "Open BPM Test Events",
              lastFolder.isEmpty() ? QStandardPaths::
                                     standardLocations(QStandardPaths::
                                                       DocumentsLocation).
                                     at(0) : lastFolder,
              "BPM test event files (*.td);;All files (*.*)");

    SimulationData *simData = new SimulationData();
    if( !filename.isNull() )
    {
        settings.setValue("lastFolder", QFileInfo(filename).absolutePath());

        if(simData->loadData(filename) > 0){
            showDashboarMessage(ERROR, tr("Event test data load founds errors, check log file for details."));
            delete simData;
            return;
        }
    }

    if(_simEngine){
        _simEngine->stop();
        delete _simEngine;
    }

    if(_simData){
        delete _simData;
        _simData = simData;
    }

    _simEngine = new SimulationEngine(currentBpm, _simData, _scene);
    connect(_simEngine, &SimulationEngine::started, [this](){
        EnableButtons(SIM_STARTED);
         showDashboarMessage(INFO, "Simulation started");
    });
    connect(_simEngine, &SimulationEngine::finished, [this](){
        EnableButtons(SIM_STOPPED);
        showDashboarMessage(INFO, "Simulation finished");
    });
    connect(_simEngine, &SimulationEngine::paused, [this](){
        EnableButtons(SIM_PAUSED);
        showDashboarMessage(INFO, "Simulation paused");
    });
    connect(_simEngine, &SimulationEngine::restarted, [this](){
        EnableButtons(SIM_RESTARTED);
        showDashboarMessage(INFO, "Simulation re-started");
    });

    connect(_simEngine, &SimulationEngine::eventChanged, [this](long event){
        ui->eventsTracker->setValue(static_cast<int>(10000000*static_cast<double>(event)/_simData->events()));
    });

    connect(_simEngine, &SimulationEngine::reconfigureIsNeeded, [this](QString msg, SimulationEngine::FailType type){
        MessageType msgType;
        switch(type){
        case SimulationEngine::PREDICTED_FAILURE:
            msgType = PREDICTED;
            break;
        case SimulationEngine::STATION_FAILURE:
            msgType = STATION;
            break;
        case SimulationEngine::GLOBAL_FAILURE:
            msgType = GLOBAL;
            break;
        }
        showDashboarMessage(msgType, msg);
    });
    _simEngine->setCurrentSpeed(static_cast<uint>(ui->speedSlider->value()));
    EnableButtons(DATA_OPENED);
    showDashboarMessage(INFO, tr("Events test data was loaded correctly."));
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

void MainWindow::showDashboarMessage(MessageType type, QString message)
{
    QString typeString;
    QString color;
    switch(type){
    case INFO:
        typeString = tr("INFO");
        color = "#00aa00";
        break;
    case WARNING:
        typeString = tr("WARNING");
        color = "#c7c000";
        break;
    case ERROR:
        typeString = tr("ERROR");
        color = "#dd0000";
        break;
    case CRITICAL:
        typeString = tr("CRITICAL");
        color = "#ff0000";
        break;
    case PREDICTED:
        typeString = tr("PR_MSG");
        color = "#da9100";
        break;
    case STATION:
        typeString = tr("PR_MSG");
        color = "#e79a73";
        break;
    case GLOBAL:
        typeString = tr("PR_MSG");
        color = "#8b8bd1";
        break;
    }
    ui->mDashboard->insertHtml(tr("<p style=\"margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\"color:%1;\">%2: %3</span><br/></p>").arg(color, typeString, message));
    ui->mDashboard->ensureCursorVisible();
}

void MainWindow::speedChanged(int value)
{
    if(_simEngine)
        _simEngine->setCurrentSpeed(static_cast<uint>(value));
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

