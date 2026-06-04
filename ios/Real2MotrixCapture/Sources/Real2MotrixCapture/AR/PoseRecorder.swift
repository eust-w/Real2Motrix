import ARKit
import simd

enum PoseRecorder {
    static func line(frame: ARFrame, frameIndex: Int) -> String {
        let transform = frame.camera.transform
        let translation = transform.columns.3
        let q = simd_quatf(transform)
        return "\(frame.timestamp),\(frameIndex),\(translation.x),\(translation.y),\(translation.z),\(q.imag.x),\(q.imag.y),\(q.imag.z),\(q.real),\(trackingState(frame.camera.trackingState))\n"
    }

    static func trackingState(_ state: ARCamera.TrackingState) -> String {
        switch state {
        case .normal:
            return "normal"
        case .notAvailable:
            return "not_available"
        case .limited(let reason):
            return "limited_\(reason)"
        @unknown default:
            return "unknown"
        }
    }
}

