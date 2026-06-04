import ARKit

final class ARFrameRecorder {
    private var lastSavedTimestamp: TimeInterval = 0
    private let interval: TimeInterval = 0.4

    func shouldSave(frame: ARFrame) -> Bool {
        if frame.timestamp - lastSavedTimestamp >= interval {
            lastSavedTimestamp = frame.timestamp
            return true
        }
        return false
    }

    func write(frame: ARFrame, index: Int, writer: CaptureFileWriter) throws {
        guard let data = ImageUtils.jpegData(from: frame.capturedImage) else { return }
        try writer.writeFrame(data, frameIndex: index)
    }
}

