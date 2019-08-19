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
#include <QApplication>
#include <QMutex>
#include <QDateTime>
#include <fstream>
#include <QDebug>

void logMessageHandler(QtMsgType type, const QMessageLogContext &context, const QString &msg);

int main(int argc, char *argv[])
{
    // Install the message handler for logging
    qInstallMessageHandler(logMessageHandler);
    QApplication::setAttribute(Qt::AA_EnableHighDpiScaling);

    QApplication a(argc, argv);
    MainWindow w;

    qInfo() << "Application " APP_NAME " Started";

    w.show();
    int exitCode = a.exec();

    qInfo() << "Application " APP_NAME " Finished";

    return exitCode;
}

void logMessageHandler(QtMsgType type, const QMessageLogContext &context, const QString &msg)
{
    static QMutex mutex;
    QMutexLocker lock(&mutex);
    QString sDate = QDateTime::currentDateTime().toString("yyyy.MM.dd hh:mm:ss");
    QString formattedLogMsg;
    static std::ofstream logFile(APP_NAME ".log", std::ios::app);

    switch (type) {
    case QtDebugMsg:
        formattedLogMsg = QString("Debug");
        break;
    case QtInfoMsg:
        formattedLogMsg = QString("Info");
        break;
    case QtWarningMsg:
        formattedLogMsg = QString("Warning");
        break;
    case QtCriticalMsg:
        formattedLogMsg = QString("Critical");
        break;
    case QtFatalMsg:
        formattedLogMsg = QString("Fatal");
    }

    formattedLogMsg = QString("%1 %2: %3 (%4:%5, %6)").arg(sDate, formattedLogMsg, msg,
                                                               QString::fromLocal8Bit(context.file),
                                                               QString::number(context.line),
                                                               QString::fromLocal8Bit(context.function));

    if(logFile.is_open()){
        logFile << qPrintable(formattedLogMsg) << std::endl;
    }
    fprintf(stderr, "%s\n", qPrintable(formattedLogMsg));
    fflush(stderr);
}
