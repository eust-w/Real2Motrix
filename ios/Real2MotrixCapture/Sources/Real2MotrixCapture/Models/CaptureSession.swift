import Foundation

enum CaptureType: String, CaseIterable, Identifiable, Codable {
    case scene = "scene"
    case object = "object"
    case tabletop = "tabletop"

    var id: String { rawValue }
}

enum CaptureMode: String, CaseIterable, Identifiable, Codable {
    case rgbFrames = "rgb_frames"
    case arkitPose = "arkit_pose"
    case rgbd = "rgbd"
    case objectOrbit = "object_orbit"
    case roomWalkthrough = "room_walkthrough"

    var id: String { rawValue }
}

struct CaptureSessionUploadResponse: Codable {
    let captureSession: CaptureSessionRecord
    let job: JobStatus

    enum CodingKeys: String, CodingKey {
        case captureSession = "capture_session"
        case job
    }
}

struct CaptureSessionRecord: Codable, Identifiable {
    let id: String
    let projectId: String
    let captureType: String
    let captureMode: String

    enum CodingKeys: String, CodingKey {
        case id
        case projectId = "project_id"
        case captureType = "capture_type"
        case captureMode = "capture_mode"
    }
}

