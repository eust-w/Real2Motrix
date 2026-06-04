import Foundation
import simd

final class CaptureFileWriter {
    let root: URL
    let captureId = UUID().uuidString
    private let encoder = JSONEncoder()

    init() throws {
        root = FileManager.default.temporaryDirectory.appendingPathComponent("capture_\(captureId)", isDirectory: true)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)
        for folder in ["frames", "poses", "depth", "confidence", "armesh", "imu", "quality"] {
            try FileManager.default.createDirectory(at: root.appendingPathComponent(folder), withIntermediateDirectories: true)
        }
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
    }

    func writeFrame(_ data: Data, frameIndex: Int) throws {
        try data.write(to: root.appendingPathComponent("frames/frame_\(String(format: "%06d", frameIndex)).jpg"))
    }

    func writeDepth(_ data: Data, frameIndex: Int) throws {
        try data.write(to: root.appendingPathComponent("depth/depth_\(String(format: "%06d", frameIndex)).png"))
    }

    func writeIntrinsics(width: Int, height: Int, matrix: simd_float3x3) throws {
        let payload: [String: Any] = [
            "camera_model": "pinhole",
            "width": width,
            "height": height,
            "fx": Double(matrix.columns.0.x),
            "fy": Double(matrix.columns.1.y),
            "cx": Double(matrix.columns.2.x),
            "cy": Double(matrix.columns.2.y),
            "distortion": [],
            "unit": "pixel"
        ]
        try JSONSerialization.data(withJSONObject: payload, options: [.prettyPrinted, .sortedKeys])
            .write(to: root.appendingPathComponent("camera_intrinsics.json"))
    }

    func writeMetadata(_ metadata: CaptureMetadata) throws {
        try encoder.encode(metadata).write(to: root.appendingPathComponent("metadata.json"))
    }

    func writeQuality(_ quality: CaptureQualityReport) throws {
        try encoder.encode(quality).write(to: root.appendingPathComponent("quality/quality_report.json"))
    }

    func writePoseHeader() throws {
        try "timestamp,frame_id,tx,ty,tz,qx,qy,qz,qw,tracking_state\n".write(
            to: root.appendingPathComponent("poses/poses.csv"),
            atomically: true,
            encoding: .utf8
        )
    }

    func appendPose(line: String) throws {
        let url = root.appendingPathComponent("poses/poses.csv")
        let handle = try FileHandle(forWritingTo: url)
        try handle.seekToEnd()
        try handle.write(contentsOf: Data(line.utf8))
        try handle.close()
    }

    func buildZip() throws -> URL {
        let destination = FileManager.default.temporaryDirectory.appendingPathComponent("capture_session_\(captureId).zip")
        try ZipBuilder().zip(directory: root, destination: destination)
        return destination
    }
}
