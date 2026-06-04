import ARKit
import SwiftUI

struct ARCaptureView: View {
    @EnvironmentObject private var appState: AppState
    @StateObject private var sessionManager = ARSessionManager()
    @State private var reviewURL: URL?

    var body: some View {
        ZStack(alignment: .bottom) {
            ARViewContainer(sessionManager: sessionManager)
                .ignoresSafeArea()
            VStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 6) {
                    Text(sessionManager.qualityWarning)
                    Text("Frames \(sessionManager.frameCount) · Blur \(sessionManager.averageBlur, specifier: "%.1f") · Brightness \(sessionManager.averageBrightness, specifier: "%.2f")")
                    if let liveSession = appState.liveSession {
                        Text("Live \(liveSession.status) · Uploaded \(liveSession.frameCount)")
                    }
                }
                .font(.caption)
                .padding(10)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(.ultraThinMaterial)
                HStack {
                    Button(sessionManager.isRecording ? "Stop" : "Record") {
                        if sessionManager.isRecording {
                            Task {
                                reviewURL = try? await sessionManager.stopCapture(appState: appState)
                            }
                        } else {
                            Task {
                                try? await sessionManager.startCapture(appState: appState)
                            }
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    if let reviewURL {
                        NavigationLink("Review", destination: CaptureReviewView(zipURL: reviewURL, hasLidar: sessionManager.hasLidar))
                            .buttonStyle(.bordered)
                    }
                }
            }
            .padding()
        }
        .navigationTitle("AR capture")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear { sessionManager.run() }
        .onDisappear { sessionManager.pause() }
    }
}

struct ARViewContainer: UIViewRepresentable {
    let sessionManager: ARSessionManager

    func makeUIView(context: Context) -> ARSCNView {
        let view = ARSCNView(frame: .zero)
        view.session = sessionManager.session
        view.automaticallyUpdatesLighting = true
        return view
    }

    func updateUIView(_ uiView: ARSCNView, context: Context) {}
}
