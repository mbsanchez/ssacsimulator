#-------------------------------------------------
#
# Project created by QtCreator 2013-04-17T09:06:06
#
#-------------------------------------------------

QT       += core gui

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

TARGET = SSACSimulator
TEMPLATE = app

DESTDIR = ../bin

#QGVCore librairie
LIBS += -L$$OUT_PWD/../lib -lQGVCore
INCLUDEPATH += $$PWD/../QGVCore
DEPENDPATH += $$PWD/../QGVCore
DEFINES += APP_NAME="\\\"$$TARGET\\\""

#GraphViz librairie
!include(../QGVCore/GraphViz.pri) {
     error("fail open GraphViz.pri")
 }

SOURCES += main.cpp\
        MainWindow.cpp \
    QGraphicsViewEc.cpp \
    businessprocess.cpp \
    simulationengine.cpp \
    simulationevent.cpp \
    smartobject.cpp

HEADERS  += MainWindow.h \
    QGraphicsViewEc.h \
    businessprocess.h \
    simulationengine.h \
    simulationevent.h \
    smartobject.h

FORMS    += MainWindow.ui

RESOURCES += \
    ress.qrc
