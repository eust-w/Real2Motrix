import SwiftUI

struct CaptureModeView: View {
    @EnvironmentObject private var state: AppState

    var body: some View {
        Form {
            Section("Capture type") {
                Picker("Type", selection: $state.captureType) {
                    ForEach(CaptureType.allCases) { type in
                        Text(type.rawValue).tag(type)
                    }
                }
                Picker("Mode", selection: $state.captureMode) {
                    ForEach(CaptureMode.allCases) { mode in
                        Text(mode.rawValue).tag(mode)
                    }
                }
            }
            Section("Guidance") {
                Label("Move slowly and keep overlap between views.", systemImage: "figure.walk.motion")
                Label("Avoid dark, reflective, and transparent surfaces.", systemImage: "lightbulb")
                Label("Collect at least 80 frames for object scans.", systemImage: "camera")
            }
            Section {
                NavigationLink("Start AR capture", destination: ARCaptureView())
            }
        }
        .navigationTitle("Capture setup")
    }
}

