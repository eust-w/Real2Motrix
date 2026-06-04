import ARKit
import UIKit

enum DeviceUtils {
    static var deviceModel: String {
        UIDevice.current.model
    }

    static var iosVersion: String {
        UIDevice.current.systemVersion
    }

    static var hasLidar: Bool {
        ARWorldTrackingConfiguration.supportsSceneReconstruction(.mesh)
    }

    static var supportsSceneDepth: Bool {
        ARWorldTrackingConfiguration.supportsFrameSemantics(.sceneDepth)
    }
}

