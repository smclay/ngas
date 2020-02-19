cmake_minimum_required(VERSION 2.8.12)

#project(ngams-C-client VERSION 11.0)
project(ngams-C-client C)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED True)
set(CMAKE_C_FLAGS "-Wall -pipe -m64 -mtune=generic -O2" )

find_package(ZLIB REQUIRED)
find_package(Threads REQUIRED)
include("FindBerkeleyDB.cmake")

add_custom_command(
    OUTPUT ngamsArchiveClientMan.txt.c
    COMMAND @bash doc2txt.sh "ngamsArchiveClientMan.doc"
    VERBATIM)

add_custom_command(
    OUTPUT ngamsCClientMan.txt.c
    COMMAND @bash doc2txt.sh "ngamsCClientMan.doc"
    VERBATIM)

add_custom_command(
    OUTPUT ngamsCClientXMan.txt.c
    COMMAND @bash doc2txt.sh "ngamsCClientXMan.doc"
    VERBATIM)

add_custom_command(
    OUTPUT ngamsLicense.txt.c
    COMMAND @bash doc2txt.sh "ngamsLicense.doc"
    VERBATIM)

add_custom_command(
    OUTPUT ngamsVERSION.h
    COMMAND @cat ../../VERSION > ngamsVERSION.h
    VERBATIM)

#configure_file(ngamsVERSION.h.in ngamsVERSION.h)

add_library(
    ngamslib
    ngamsVERSION.h
    ngamsCClientLib.c)

set_target_properties(ngamslib PROPERTIES LINKER_LANGUAGE C)

add_executable(
    ngamsCClient
    ngamsCClient.c
    ngamsCClientMan.txt.c
    ngamsLicense.txt.c
    ngamsVERSION.h)

add_executable(
    ngamsCClientX
    ngamsCClientX.c
    ngamsCClientXMan.txt.c
    ngamsLicense.txt.c)

add_executable(
    ngamsArchiveClient
    ngamsArchiveClient.c
    ngamsArchiveClientMan.txt.c
    ngamsLicense.txt.c)

add_executable(
    ngamsCrc32
    ngamsCrc32.c)

target_link_libraries(
    ngamsCClient
    PUBLIC m
    PRIVATE ngamslib)

target_link_libraries(
    ngamsCClientX
    PUBLIC m
    PRIVATE ngamslib)

target_link_libraries(
    ngamsArchiveClient
    PUBLIC m
    PUBLIC ${CMAKE_THREAD_LIBS_INIT}
    PUBLIC ${BerkeleyDB_LIBRARIES}
    PRIVATE ngamslib)

target_link_libraries(
    ngamsCrc32
    PUBLIC m
    PUBLIC ${ZLIB_LIBRARIES}
    PRIVATE ngamslib)

