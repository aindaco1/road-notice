import Foundation

enum AppLinks {
    static let website = URL(string: "https://finemenot.xyz/")!
    static let publicDatabase = website.appending(path: "data", directoryHint: .isDirectory)
    // A private test archive can pin reviewed inputs without changing the
    // downloader or publishing candidate data to the public update feed.
    static let database: URL = {
        if let value = Bundle.main.object(forInfoDictionaryKey: "CameraDatabaseURL") as? String,
           let url = URL(string: value), url.scheme == "https", url.host != nil {
            return url
        }
        return publicDatabase
    }()
}
