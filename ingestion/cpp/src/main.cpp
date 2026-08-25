#include <iostream>
#include <string>
#include <vector>
#include <cmath>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp/serialization.hpp"
#include "rosbag2_cpp/reader.hpp"
#include "geometry_msgs/msg/pose_with_covariance_stamped.hpp"

#include "postgres_writer.hpp"

namespace {

// theta desde quaternion — fórmula general (funciona aunque x=y=0, que es
// el caso de un robot 2D como slam_bot).
double yaw_from_quaternion(double x, double y, double z, double w) {
    return std::atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z));
}

// timestamp de un mensaje de bag -> segundos (double), en base al header.
double header_stamp_to_seconds(const geometry_msgs::msg::PoseWithCovarianceStamped& msg) {
    return static_cast<double>(msg.header.stamp.sec) +
           static_cast<double>(msg.header.stamp.nanosec) * 1e-9;
}

constexpr size_t BATCH_SIZE = 500;

}  

int main(int argc, char** argv) {
    if (argc < 4) {
        std::cerr << "Uso: ingest_run <bag_path> <experiment_id> <connection_string>\n";
        return 1;
    }

    const std::string bag_path = argv[1];
    const int experiment_id = std::stoi(argv[2]);
    const std::string connstr = argv[3];

    const std::string target_topic = "/slam/pose_covariance";

    PostgresWriter writer(connstr);
    const int run_id = writer.create_run(experiment_id, bag_path);
    std::cout << "Creado run_id=" << run_id << " para bag " << bag_path << "\n";

    rosbag2_cpp::Reader reader;
    reader.open(bag_path);

    rclcpp::Serialization<geometry_msgs::msg::PoseWithCovarianceStamped> serialization;

    std::vector<PostgresWriter::TelemetryRow> batch;
    batch.reserve(BATCH_SIZE);

    bool have_t0 = false;
    double t0 = 0.0;

    size_t total_messages = 0;
    size_t matched_messages = 0;

    while (reader.has_next()) {
        auto bag_message = reader.read_next();
        total_messages++;

        if (bag_message->topic_name != target_topic) {
            continue;
        }
        matched_messages++;

        geometry_msgs::msg::PoseWithCovarianceStamped msg;
        rclcpp::SerializedMessage serialized_msg(*bag_message->serialized_data);
        serialization.deserialize_message(&serialized_msg, &msg);

        const double t_abs = header_stamp_to_seconds(msg);
        if (!have_t0) {
            t0 = t_abs;
            have_t0 = true;
        }

        PostgresWriter::TelemetryRow row{};
        row.t_seconds = t_abs - t0;
        row.x = msg.pose.pose.position.x;
        row.y = msg.pose.pose.position.y;
        row.theta = yaw_from_quaternion(
            msg.pose.pose.orientation.x,
            msg.pose.pose.orientation.y,
            msg.pose.pose.orientation.z,
            msg.pose.pose.orientation.w
        );

        row.cov_xx = msg.pose.covariance[0];
        row.cov_yy = msg.pose.covariance[7];
        row.cov_tt = msg.pose.covariance[35];

        row.linear_vel = 0.0;
        row.angular_vel = 0.0;

        batch.push_back(row);

        if (batch.size() >= BATCH_SIZE) {
            writer.insert_telemetry_batch(run_id, batch);
            std::cout << "Insertado batch de " << batch.size() << " filas...\n";
            batch.clear();
        }
    }

    if (!batch.empty()) {
        writer.insert_telemetry_batch(run_id, batch);
        std::cout << "Insertado batch final de " << batch.size() << " filas.\n";
    }

    writer.mark_run_complete(run_id);

    std::cout << "Ingesta completa para run_id=" << run_id << "\n"
              << "Mensajes totales en bag: " << total_messages << "\n"
              << "Mensajes de " << target_topic << ": " << matched_messages << "\n";

    return 0;
}
