import ARKit

final class DepthRecorder {
    private(set) var depthFrameCount = 0

    func write(frame: ARFrame, index: Int, writer: CaptureFileWriter) throws {
        guard let sceneDepth = frame.sceneDepth,
              let data = ImageUtils.pngData(from: sceneDepth.depthMap) else {
            return
        }
        try writer.writeDepth(data, frameIndex: index)
        depthFrameCount += 1
    }
}

