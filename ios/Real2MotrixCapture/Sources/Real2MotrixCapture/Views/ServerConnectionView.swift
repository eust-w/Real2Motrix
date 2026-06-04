import SwiftUI

struct ServerConnectionView: View {
    @EnvironmentObject private var state: AppState

    var body: some View {
        Form {
            Section("Backend") {
                TextField("http://192.168.1.10:8000", text: $state.serverURLText)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.URL)
                Button("Test connection") {
                    Task { await state.testConnection() }
                }
                Text(state.connectionMessage)
                    .foregroundStyle(state.connectionMessage == "Connected" ? .green : .secondary)
            }
            Section {
                NavigationLink("Projects", destination: ProjectListView())
                    .disabled(state.connectionMessage != "Connected")
            }
        }
        .navigationTitle("Real2Motrix Capture")
    }
}

