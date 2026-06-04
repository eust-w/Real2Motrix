import Foundation

struct CaptureMetadata: Codable {
    let app: String
    let captureId: String
    let projectId: String
    let captureType: String
    let captureMode: String
    let deviceModel: String
    let iosVersion: String
    let hasLidar: Bool
    let hasDepth: Bool
    let hasArkitPose: Bool
    let unit: String
    let coordinateSystem: String
    let frameCount: Int
    let depthFrameCount: Int
    let resolution: [Int]
    let createdAt: String
    let durationSeconds: Double

    enum CodingKeys: String, CodingKey {
        case app
        case captureId = "capture_id"
        case projectId = "project_id"
        case captureType = "capture_type"
        case captureMode = "capture_mode"
        case deviceModel = "device_model"
        case iosVersion = "ios_version"
        case hasLidar = "has_lidar"
        case hasDepth = "has_depth"
        case hasArkitPose = "has_arkit_pose"
        case unit
        case coordinateSystem = "coordinate_system"
        case frameCount = "frame_count"
        case depthFrameCount = "depth_frame_count"
        case resolution
        case createdAt = "created_at"
        case durationSeconds = "duration_seconds"
    }
}

struct CaptureQualityReport: Codable {
    var frameCount: Int
    var averageBrightness: Double
    var averageBlurScore: Double
    var trackingLostCount: Int
    var averageCameraSpeedMps: Double
    var coverageScore: Double
    var warnings: [String]

    enum CodingKeys: String, CodingKey {
        case frameCount = "frame_count"
        case averageBrightness = "average_brightness"
        case averageBlurScore = "average_blur_score"
        case trackingLostCount = "tracking_lost_count"
        case averageCameraSpeedMps = "average_camera_speed_mps"
        case coverageScore = "coverage_score"
        case warnings
    }
}

