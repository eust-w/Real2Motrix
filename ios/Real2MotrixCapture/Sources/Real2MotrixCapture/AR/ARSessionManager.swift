import ARKit
import Combine
import Foundation
import simd

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
    private var liveClient: LiveScanClient?
    private var liveProjectId: String?
    private var liveSession: LiveScanSessionRecord?
    private var lastMeshUploadAt = Date.distantPast

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

    func startCapture(appState: AppState) async throws {
        guard let project = appState.selectedProject, let client = appState.apiClient else { return }
        liveClient = LiveScanClient(apiClient: client)
        liveProjectId = project.id
        liveSession = try await liveClient?.createSession(
            projectId: project.id,
            captureType: appState.captureType,
            captureMode: appState.captureMode,
            deviceModel: DeviceUtils.deviceModel,
            hasLidar: DeviceUtils.hasLidar
        )
        appState.liveSession = liveSession
        writer = try CaptureFileWriter()
        try writer?.writePoseHeader()
        frameCount = 0
        wroteIntrinsics = false
        qualityAnalyzer = QualityAnalyzer()
        startedAt = Date()
        lastMeshUploadAt = .distantPast
        isRecording = true
        qualityWarning = "Recording live"
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
        if let liveClient, let liveProjectId, let liveSession {
            do {
                let response = try await liveClient.finish(projectId: liveProjectId, sessionId: liveSession.id)
                self.liveSession = response.liveSession
                appState.liveSession = response.liveSession
                appState.jobStatus = response.job
            } catch {
                qualityWarning = "Live finish failed: \(error.localizedDescription)"
            }
        }
        self.writer = nil
        self.liveClient = nil
        self.liveProjectId = nil
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
                guard let imageData = frameRecorder.imageData(frame: frame) else { return }
                try writer.writeFrame(imageData, frameIndex: frameCount)
                try writer.appendPose(line: PoseRecorder.line(frame: frame, frameIndex: frameCount))
                try depthRecorder.write(frame: frame, index: frameCount, writer: writer)
                uploadLiveFrame(frame: frame, frameIndex: frameCount, imageData: imageData)
            } catch {
                qualityWarning = "Write failed: \(error.localizedDescription)"
            }
        }
    }

    nonisolated func session(_ session: ARSession, didAdd anchors: [ARAnchor]) {
        Task { @MainActor in
            anchors.compactMap { $0 as? ARMeshAnchor }.forEach(meshExporter.capture)
            uploadLiveMeshSnapshotIfNeeded()
        }
    }

    nonisolated func session(_ session: ARSession, didUpdate anchors: [ARAnchor]) {
        Task { @MainActor in
            anchors.compactMap { $0 as? ARMeshAnchor }.forEach(meshExporter.capture)
            uploadLiveMeshSnapshotIfNeeded()
        }
    }

    private func uploadLiveFrame(frame: ARFrame, frameIndex: Int, imageData: Data) {
        guard let liveClient, let liveProjectId, let liveSession else { return }
        let poseJSON = jsonString(posePayload(frame: frame))
        let qualityJSON = jsonString([
            "brightness": averageBrightness,
            "blur_score": averageBlur,
            "tracking_state": PoseRecorder.trackingState(frame.camera.trackingState)
        ])
        let intrinsicsJSON = jsonString(intrinsicsPayload(frame: frame))
        let timestamp = frame.timestamp
        Task {
            do {
                let updated = try await liveClient.uploadFrame(
                    projectId: liveProjectId,
                    sessionId: liveSession.id,
                    frameIndex: frameIndex,
                    timestamp: timestamp,
                    imageData: imageData,
                    poseJSON: poseJSON,
                    qualityJSON: qualityJSON,
                    intrinsicsJSON: intrinsicsJSON
                )
                self.liveSession = updated
                qualityWarning = "Live uploaded \(updated.frameCount) frames"
            } catch {
                qualityWarning = "Live upload failed: \(error.localizedDescription)"
            }
        }
    }

    private func uploadLiveMeshSnapshotIfNeeded() {
        guard isRecording, let liveClient, let liveProjectId, let liveSession else { return }
        let now = Date()
        guard now.timeIntervalSince(lastMeshUploadAt) >= 1.2 else { return }
        let obj = meshExporter.objString()
        guard !obj.isEmpty, let data = obj.data(using: .utf8) else { return }
        lastMeshUploadAt = now
        Task {
            do {
                let updated = try await liveClient.uploadMeshChunk(
                    projectId: liveProjectId,
                    sessionId: liveSession.id,
                    chunkIndex: 0,
                    objData: data
                )
                self.liveSession = updated
            } catch {
                qualityWarning = "Live mesh upload failed: \(error.localizedDescription)"
            }
        }
    }

    private func posePayload(frame: ARFrame) -> [String: Any] {
        let transform = frame.camera.transform
        let translation = transform.columns.3
        let q = simd_quatf(transform)
        return [
            "position": [Double(translation.x), Double(translation.y), Double(translation.z)],
            "quaternion": [Double(q.imag.x), Double(q.imag.y), Double(q.imag.z), Double(q.real)],
            "tracking_state": PoseRecorder.trackingState(frame.camera.trackingState),
            "timestamp": frame.timestamp
        ]
    }

    private func intrinsicsPayload(frame: ARFrame) -> [String: Any] {
        let pixelBuffer = frame.capturedImage
        let matrix = frame.camera.intrinsics
        return [
            "camera_model": "pinhole",
            "width": CVPixelBufferGetWidth(pixelBuffer),
            "height": CVPixelBufferGetHeight(pixelBuffer),
            "fx": Double(matrix.columns.0.x),
            "fy": Double(matrix.columns.1.y),
            "cx": Double(matrix.columns.2.x),
            "cy": Double(matrix.columns.2.y),
            "distortion": [],
            "unit": "pixel"
        ]
    }

    private func jsonString(_ payload: [String: Any]) -> String {
        guard JSONSerialization.isValidJSONObject(payload),
              let data = try? JSONSerialization.data(withJSONObject: payload),
              let string = String(data: data, encoding: .utf8) else {
            return "{}"
        }
        return string
    }
}
