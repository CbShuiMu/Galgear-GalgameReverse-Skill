// GalSkill CLI adaptation, 2026-10-22. GPL-3.0-or-later.
// Replaces GalArc's GUI configuration, progress UI and CString helper.
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace ArcFormats {
    public static class Config {
        public static Encoding Encoding = Encoding.GetEncoding(932,
            EncoderFallback.ExceptionFallback, DecoderFallback.ExceptionFallback);
    }
}
namespace Log {
    public static class LogUtility {
        public static void ErrorInvalidArchive() { throw new InvalidDataException("Invalid archive header."); }
        public static void InitBar(long count) { }
        public static void UpdateBar() { }
    }
}
namespace Utility.Extensions {
    public static class BinaryReaderExtensions {
        public static string ReadCString(this BinaryReader reader, Encoding encoding, byte terminator) {
            var bytes = new List<byte>();
            for (;;) {
                byte value = reader.ReadByte();
                if (value == terminator) return encoding.GetString(bytes.ToArray());
                bytes.Add(value);
            }
        }
    }
}
