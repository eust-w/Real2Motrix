import ARKit

enum IntrinsicsExtractor {
    static func writeIfNeeded(frame: ARFrame, writer: CaptureFileWriter, didWrite: inout Bool) throws {
        guard !didWrite else { return }
        let pixelBuffer = frame.capturedImage
        try writer.writeIntrinsics(
            width: CVPixelBufferGetWidth(pixelBuffer),
            height: CVPixelBufferGetHeight(pixelBuffer),
            matrix: frame.camera.intrinsics
        )
        didWrite = true
    }
}

