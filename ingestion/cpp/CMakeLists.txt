cmake_minimum_required(VERSION 3.16)
project(robo_diagnostics_ingestion)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Requiere un entorno con ROS2 instalado (source /opt/ros/<distro>/setup.bash
# antes de correr cmake). No se compila en este sandbox — es el punto de
# partida para tu máquina/VM con ROS2.
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rosbag2_cpp REQUIRED)
find_package(rosbag2_storage REQUIRED)
find_package(geometry_msgs REQUIRED)

# libpqxx para escribir a Postgres desde C++.
# Instala con: sudo apt install libpqxx-dev
find_package(PkgConfig REQUIRED)
pkg_check_modules(PQXX REQUIRED libpqxx)

add_executable(ingest_run
    src/main.cpp
    src/postgres_writer.cpp
)

target_include_directories(ingest_run PRIVATE include ${PQXX_INCLUDE_DIRS})
target_link_libraries(ingest_run ${PQXX_LIBRARIES})
ament_target_dependencies(ingest_run rclcpp rosbag2_cpp rosbag2_storage geometry_msgs)

install(TARGETS ingest_run DESTINATION lib/${PROJECT_NAME})

ament_package()
