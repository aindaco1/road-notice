import Foundation

public struct Coordinate: Codable, Hashable, Sendable {
    public var latitude: Double
    public var longitude: Double
    public init(_ latitude: Double, _ longitude: Double) {
        self.latitude = latitude
        self.longitude = longitude
    }
    public var isValid: Bool {
        latitude.isFinite && longitude.isFinite && (-90...90).contains(latitude) && (-180...180).contains(longitude)
    }
}

public enum CameraKind: String, Codable, Sendable {
    case speed, redLight, speedAndRedLight, possibleSpeed
    public var title: String {
        switch self {
        case .speed: "Speed camera"
        case .redLight: "Red-light camera"
        case .speedAndRedLight: "Speed and red-light camera"
        case .possibleSpeed: "Possible speed camera"
        }
    }
}

public struct Camera: Codable, Identifiable, Hashable, Sendable {
    public let id: String
    public let siteID: String
    public let label: String
    public let kind: CameraKind
    /// One coordinate is a point; two or more form a verified road polyline.
    public let geometry: [Coordinate]
    public let travelBearing: Double?
    public let sourceIDs: [String]
    public let evidence: String
    public let validUntil: Date?
    public let speedLimit: SpeedLimit?
    public let roadZone: RoadZone?

    public init(id: String, siteID: String? = nil, label: String, kind: CameraKind,
                geometry: [Coordinate], travelBearing: Double? = nil,
                sourceIDs: [String] = [], evidence: String = "", validUntil: Date? = nil,
                speedLimit: SpeedLimit? = nil, roadZone: RoadZone? = nil) {
        self.id = id; self.siteID = siteID ?? id; self.label = label; self.kind = kind
        self.geometry = geometry; self.travelBearing = travelBearing
        self.sourceIDs = sourceIDs; self.evidence = evidence; self.validUntil = validUntil
        self.speedLimit = speedLimit
        self.roadZone = roadZone
    }
}

public struct DatasetSource: Codable, Sendable {
    public let id: String
    public let name: String
    public let url: String
    public let license: String
    public let checkedAt: Date
    public let status: String
}

public struct CameraSnapshot: Codable, Sendable {
    public let schemaVersion: Int
    public let version: String
    public let generatedAt: Date
    public let coverage: String
    public let sources: [DatasetSource]
    public let cameras: [Camera]

    public func validate(now: Date = .now) throws {
        guard schemaVersion == 1, !version.isEmpty, cameras.count <= 100_000,
              generatedAt <= now.addingTimeInterval(86400) else { throw DatabaseError.invalidSnapshot }
        guard Set(cameras.map(\.id)).count == cameras.count else { throw DatabaseError.duplicateID }
        for camera in cameras {
            guard !camera.id.isEmpty, !camera.siteID.isEmpty, !camera.label.isEmpty,
                  !camera.geometry.isEmpty, camera.geometry.count <= 2000,
                  camera.geometry.allSatisfy(\.isValid), !camera.sourceIDs.isEmpty,
                  !camera.evidence.isEmpty else { throw DatabaseError.invalidCamera(camera.id) }
            if let bearing = camera.travelBearing, !bearing.isFinite || !(0..<360).contains(bearing) {
                throw DatabaseError.invalidCamera(camera.id)
            }
            if let zone = camera.roadZone, !zone.isValid { throw DatabaseError.invalidCamera(camera.id) }
            if camera.geometry.count > 1 {
                guard camera.kind == .possibleSpeed else { throw DatabaseError.invalidCamera(camera.id) }
                let span = camera.geometry.dropFirst().reduce(0.0) { max($0, Geometry.distance(camera.geometry[0], $1)) }
                guard span < 50_000 else { throw DatabaseError.invalidCamera(camera.id) }
            }
        }
    }
    public static func decode(_ data: Data) throws -> Self {
        let decoder = JSONDecoder(); decoder.dateDecodingStrategy = .iso8601
        return try decoder.decode(Self.self, from: data)
    }
}

public enum DatabaseError: Error, LocalizedError {
    case invalidSnapshot, duplicateID, invalidCamera(String), checksum, invalidManifest, rollback
    public var errorDescription: String? {
        switch self {
        case .invalidSnapshot: "The camera database is invalid. The previous database is still available."
        case .duplicateID: "The database contains duplicate camera IDs."
        case .invalidCamera: "A camera record needs review."
        case .checksum: "The database download failed its integrity check."
        case .invalidManifest: "The update manifest is invalid."
        case .rollback: "The downloaded database is older than the installed version."
        }
    }
}
