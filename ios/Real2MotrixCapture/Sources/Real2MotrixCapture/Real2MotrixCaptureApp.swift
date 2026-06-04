import SwiftUI

@main
struct Real2MotrixCaptureApp: App {
    @StateObject private var state = AppState()

    var body: some Scene {
        WindowGroup {
            NavigationStack {
                ServerConnectionView()
            }
            .environmentObject(state)
        }
    }
}

