import ARKit
import Combine
import Foundation

@MainActor
final class ARSessionManager: NSObject, ObservableObject, ARSessionDelegate {
    let session = ARSession()
    @Published var isRecording = false
    @Published var frameCount = 0
    @Published var averageBrightness = 0.0
    @Published var averageBlur = 0.0
    @Published var qualityWarning = "Ready"

    var hasLidar: Bool { DeviceUtils.hasLidar }
    private var writer: CaptureFileWriter?
    private let frameRecorder = ARFrameRecorder()
    private let depthRecorder = DepthRecorder()
    private let meshExporter = MeshAnchorExporter()
    private var qualityAnalyzer = QualityAnalyzer()
    private var wroteIntrinsics = false
    private var startedAt = Date()
    private var resolution = [0, 0]

    override init() {
        super.init()
        session.delegate = self
    }

    func run() {
        let config = ARWorldTrackingConfiguration()
        if DeviceUtils.supportsSceneDepth {
            config.frameSemantics.insert(.sceneDepth)
        }
        if ARWorldTrackingConfiguration.supportsSceneReconstruction(.mesh) {
            config.sceneReconstruction = .mesh
        }
        session.run(config)
    }

    func pause() {
        session.pause()
    }

    func startCapture(appState: AppState) throws {
        guard appState.selectedProject != nil else { return }
        writer = try CaptureFileWriter()
        try writer?.writePoseHeader()
        frameCount = 0
        wroteIntrinsics = false
        qualityAnalyzer = QualityAnalyzer()
        startedAt = Date()
        isRecording = true
        qualityWarning = "Recording"
    }

    func stopCapture(appState: AppState) async throws -> URL? {
        isRecording = false
        guard let writer, let project = appState.selectedProject else { return nil }
        let duration = Date().timeIntervalSince(startedAt)
        let metadata = CaptureMetadata(
            app: "Real2Motrix Capture",
            captureId: writer.captureId,
            projectId: project.id,
            captureType: appState.captureType.rawValue,
            captureMode: appState.captureMode.rawValue,
            deviceModel: DeviceUtils.deviceModel,
            iosVersion: DeviceUtils.iosVersion,
            hasLidar: DeviceUtils.hasLidar,
            hasDepth: depthRecorder.depthFrameCount > 0,
            hasArkitPose: true,
            unit: "meter",
            coordinateSystem: "arkit_world",
            frameCount: frameCount,
            depthFrameCount: depthRecorder.depthFrameCount,
            resolution: resolution,
            createdAt: ISO8601DateFormatter().string(from: Date()),
            durationSeconds: duration
        )
        try writer.writeMetadata(metadata)
        try writer.writeQuality(qualityAnalyzer.report(frameCount: frameCount))
        try meshExporter.writeOBJ(to: writer.root.appendingPathComponent("armesh/arkit_mesh.obj"))
        let zip = try writer.buildZip()
        appState.lastZipURL = zip
        self.writer = nil
        qualityWarning = "Capture packaged"
        return zip
    }

    nonisolated func session(_ session: ARSession, didUpdate frame: ARFrame) {
        Task { @MainActor in
            guard isRecording, let writer else { return }
            qualityAnalyzer.observe(frame: frame)
            averageBrightness = qualityAnalyzer.averageBrightness
            averageBlur = qualityAnalyzer.averageBlur
            qualityWarning = qualityAnalyzer.report(frameCount: frameCount).warnings.first ?? "Coverage looks usable"
            guard frameRecorder.shouldSave(frame: frame) else { return }
            frameCount += 1
            do {
                try IntrinsicsExtractor.writeIfNeeded(frame: frame, writer: writer, didWrite: &wroteIntrinsics)
                resolution = [CVPixelBufferGetWidth(frame.capturedImage), CVPixelBufferGetHeight(frame.capturedImage)]
                try frameRecorder.write(frame: frame, index: frameCount, writer: writer)
                try writer.appendPose(line: PoseRecorder.line(frame: frame, frameIndex: frameCount))
                try depthRecorder.write(frame: frame, index: frameCount, writer: writer)
            } catch {
                qualityWarning = "Write failed: \(error.localizedDescription)"
            }
        }
    }

    nonisolated func session(_ session: ARSession, didAdd anchors: [ARAnchor]) {
        Task { @MainActor in
            anchors.compactMap { $0 as? ARMeshAnchor }.forEach(meshExporter.capture)
        }
    }

    nonisolated func session(_ session: ARSession, didUpdate anchors: [ARAnchor]) {
        Task { @MainActor in
            anchors.compactMap { $0 as? ARMeshAnchor }.forEach(meshExporter.capture)
        }
    }
}
