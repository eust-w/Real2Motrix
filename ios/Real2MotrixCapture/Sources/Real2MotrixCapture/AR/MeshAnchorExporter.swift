import ARKit

final class MeshAnchorExporter {
    private var anchors: [ARMeshAnchor] = []

    func capture(anchor: ARMeshAnchor) {
        anchors.removeAll { $0.identifier == anchor.identifier }
        anchors.append(anchor)
    }

    func writeOBJ(to url: URL) throws {
        guard !anchors.isEmpty else { return }
        var output = ""
        var vertexOffset = 0
        for anchor in anchors {
            let geometry = anchor.geometry
            let vertices = geometry.vertices
            let faces = geometry.faces
            for index in 0..<vertices.count {
                let vertex = vertex(at: index, source: vertices)
                let world = anchor.transform * SIMD4<Float>(vertex.x, vertex.y, vertex.z, 1)
                output += "v \(world.x) \(world.y) \(world.z)\n"
            }
            for faceIndex in 0..<faces.count {
                let indices = faceIndices(faceIndex: faceIndex, source: faces).map { $0 + 1 + vertexOffset }
                if indices.count >= 3 {
                    output += "f \(indices.map(String.init).joined(separator: " "))\n"
                }
            }
            vertexOffset += vertices.count
        }
        try output.write(to: url, atomically: true, encoding: .utf8)
    }

    private func vertex(at index: Int, source: ARGeometrySource) -> SIMD3<Float> {
        let stride = source.stride
        let offset = source.offset + index * stride
        let pointer = source.buffer.contents().advanced(by: offset).assumingMemoryBound(to: Float.self)
        return SIMD3<Float>(pointer[0], pointer[1], pointer[2])
    }

    private func faceIndices(faceIndex: Int, source: ARGeometryElement) -> [Int] {
        let bytesPerIndex = source.bytesPerIndex
        let pointer = source.buffer.contents().advanced(by: faceIndex * source.indexCountPerPrimitive * bytesPerIndex)
        return (0..<source.indexCountPerPrimitive).map { i in
            if bytesPerIndex == 2 {
                return Int(pointer.advanced(by: i * bytesPerIndex).assumingMemoryBound(to: UInt16.self).pointee)
            }
            return Int(pointer.advanced(by: i * bytesPerIndex).assumingMemoryBound(to: UInt32.self).pointee)
        }
    }
}

