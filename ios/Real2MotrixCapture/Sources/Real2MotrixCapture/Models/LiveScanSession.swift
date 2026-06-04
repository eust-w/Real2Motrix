import Foundation

struct LiveScanSessionRecord: Codable, Identifiable {
    let id: String
    let projectId: String
    let status: String
    let captureType: String
    let captureMode: String
    let targetType: String
    let deviceModel: String
    let hasLidar: Bool
    let frameCount: Int
    let depthFrameCount: Int
    let meshChunkCount: Int

    enum CodingKeys: String, CodingKey {
        case id
        case projectId = "project_id"
        case status
        case captureType = "capture_type"
        case captureMode = "capture_mode"
        case targetType = "target_type"
        case deviceModel = "device_model"
        case hasLidar = "has_lidar"
        case frameCount = "frame_count"
        case depthFrameCount = "depth_frame_count"
        case meshChunkCount = "mesh_chunk_count"
    }
}

struct LiveScanFinishResponse: Codable {
    let liveSession: LiveScanSessionRecord
    let job: JobStatus

    enum CodingKeys: String, CodingKey {
        case liveSession = "live_session"
        case job
    }
}
