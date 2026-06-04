import Foundation

final class ZipBuilder {
    func zip(directory: URL, destination: URL) throws {
        let files = try FileManager.default.subpathsOfDirectory(atPath: directory.path)
            .map { directory.appendingPathComponent($0) }
            .filter { url in
                var isDirectory: ObjCBool = false
                FileManager.default.fileExists(atPath: url.path, isDirectory: &isDirectory)
                return !isDirectory.boolValue
            }

        var output = Data()
        var central = Data()
        var offset: UInt32 = 0

        for fileURL in files {
            let name = fileURL.path.replacingOccurrences(of: directory.path + "/", with: "")
            let fileData = try Data(contentsOf: fileURL)
            let crc = CRC32.checksum(fileData)
            let nameData = Data(name.utf8)
            let localOffset = offset

            output.appendLE(0x04034b50 as UInt32)
            output.appendLE(20 as UInt16)
            output.appendLE(0 as UInt16)
            output.appendLE(0 as UInt16)
            output.appendLE(0 as UInt16)
            output.appendLE(0 as UInt16)
            output.appendLE(crc)
            output.appendLE(UInt32(fileData.count))
            output.appendLE(UInt32(fileData.count))
            output.appendLE(UInt16(nameData.count))
            output.appendLE(0 as UInt16)
            output.append(nameData)
            output.append(fileData)
            offset = UInt32(output.count)

            central.appendLE(0x02014b50 as UInt32)
            central.appendLE(20 as UInt16)
            central.appendLE(20 as UInt16)
            central.appendLE(0 as UInt16)
            central.appendLE(0 as UInt16)
            central.appendLE(0 as UInt16)
            central.appendLE(0 as UInt16)
            central.appendLE(crc)
            central.appendLE(UInt32(fileData.count))
            central.appendLE(UInt32(fileData.count))
            central.appendLE(UInt16(nameData.count))
            central.appendLE(0 as UInt16)
            central.appendLE(0 as UInt16)
            central.appendLE(0 as UInt16)
            central.appendLE(0 as UInt16)
            central.appendLE(0 as UInt32)
            central.appendLE(localOffset)
            central.append(nameData)
        }

        let centralOffset = UInt32(output.count)
        output.append(central)
        output.appendLE(0x06054b50 as UInt32)
        output.appendLE(0 as UInt16)
        output.appendLE(0 as UInt16)
        output.appendLE(UInt16(files.count))
        output.appendLE(UInt16(files.count))
        output.appendLE(UInt32(central.count))
        output.appendLE(centralOffset)
        output.appendLE(0 as UInt16)
        try output.write(to: destination, options: .atomic)
    }
}

private enum CRC32 {
    static let table: [UInt32] = (0..<256).map { i in
        var c = UInt32(i)
        for _ in 0..<8 {
            c = (c & 1) == 1 ? 0xedb88320 ^ (c >> 1) : c >> 1
        }
        return c
    }

    static func checksum(_ data: Data) -> UInt32 {
        var crc: UInt32 = 0xffffffff
        for byte in data {
            crc = table[Int((crc ^ UInt32(byte)) & 0xff)] ^ (crc >> 8)
        }
        return crc ^ 0xffffffff
    }
}

private extension Data {
    mutating func appendLE(_ value: UInt16) {
        var little = value.littleEndian
        append(Data(bytes: &little, count: MemoryLayout<UInt16>.size))
    }

    mutating func appendLE(_ value: UInt32) {
        var little = value.littleEndian
        append(Data(bytes: &little, count: MemoryLayout<UInt32>.size))
    }
}

