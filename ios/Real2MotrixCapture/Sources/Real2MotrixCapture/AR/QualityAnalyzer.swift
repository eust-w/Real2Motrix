import ARKit
import simd

final class QualityAnalyzer {
    private(set) var brightnessValues: [Double] = []
    private(set) var blurValues: [Double] = []
    private(set) var trackingLostCount = 0
    private var lastTimestamp: TimeInterval?
    private var lastPosition: SIMD3<Float>?
    private(set) var speeds: [Double] = []
    private(set) var positions: [SIMD3<Float>] = []

    func observe(frame: ARFrame) {
        brightnessValues.append(ImageUtils.brightness(from: frame.capturedImage))
        blurValues.append(ImageUtils.blurScore(from: frame.capturedImage))
        if case .normal = frame.camera.trackingState {
        } else {
            trackingLostCount += 1
        }
        let position = SIMD3<Float>(
            frame.camera.transform.columns.3.x,
            frame.camera.transform.columns.3.y,
            frame.camera.transform.columns.3.z
        )
        positions.append(position)
        if let lastTimestamp, let lastPosition {
            let dt = max(frame.timestamp - lastTimestamp, 0.001)
            speeds.append(Double(simd_distance(position, lastPosition)) / dt)
        }
        lastTimestamp = frame.timestamp
        lastPosition = position
    }

    var averageBrightness: Double {
        average(brightnessValues)
    }

    var averageBlur: Double {
        average(blurValues)
    }

    func report(frameCount: Int) -> CaptureQualityReport {
        var warnings: [String] = []
        if frameCount < 80 { warnings.append("Frame count is below the recommended minimum of 80.") }
        if averageBrightness < 0.18 { warnings.append("Lighting appears too dark.") }
        if averageBlur < 20 { warnings.append("Images may be blurry.") }
        if average(speeds) > 0.5 { warnings.append("Camera movement is too fast.") }
        if trackingLostCount > 0 { warnings.append("ARKit tracking was limited or unavailable for some frames.") }
        return CaptureQualityReport(
            frameCount: frameCount,
            averageBrightness: averageBrightness,
            averageBlurScore: averageBlur,
            trackingLostCount: trackingLostCount,
            averageCameraSpeedMps: average(speeds),
            coverageScore: coverageScore(),
            warnings: warnings
        )
    }

    private func coverageScore() -> Double {
        guard positions.count > 1 else { return 0 }
        let xs = positions.map { $0.x }
        let ys = positions.map { $0.y }
        let zs = positions.map { $0.z }
        let spread = (xs.max()! - xs.min()!) + (ys.max()! - ys.min()!) + (zs.max()! - zs.min()!)
        return min(1.0, Double(spread) / 3.0)
    }

    private func average(_ values: [Double]) -> Double {
        values.isEmpty ? 0 : values.reduce(0, +) / Double(values.count)
    }
}
