import SwiftUI

struct ProjectListView: View {
    @EnvironmentObject private var state: AppState
    @State private var newProjectName = ""

    var body: some View {
        List {
            Section("Create") {
                TextField("Project name", text: $newProjectName)
                Button("Create project") {
                    Task {
                        await state.createProject(name: newProjectName)
                        newProjectName = ""
                    }
                }
                .disabled(newProjectName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
            Section("Existing") {
                ForEach(state.projects) { project in
                    Button {
                        state.selectedProject = project
                    } label: {
                        HStack {
                            VStack(alignment: .leading) {
                                Text(project.name)
                                Text(project.status).font(.caption).foregroundStyle(.secondary)
                            }
                            Spacer()
                            if state.selectedProject?.id == project.id {
                                Image(systemName: "checkmark.circle.fill").foregroundStyle(.green)
                            }
                        }
                    }
                }
            }
            Section {
                NavigationLink("Capture setup", destination: CaptureModeView())
                    .disabled(state.selectedProject == nil)
            }
        }
        .navigationTitle("Projects")
        .task {
            await state.testConnection()
        }
    }
}

