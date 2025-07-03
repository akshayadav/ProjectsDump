//
//  Item.swift
//  ShortcutOnWakeSample
//
//  Created by Akshay Yadav on 5/29/25.
//

import Foundation
import SwiftData

@Model
final class Item: Identifiable {
    let id = UUID()
    var timestamp: Date
    
    init(timestamp: Date) {
        self.timestamp = timestamp
    }
}
