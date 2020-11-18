from struct import pack, unpack, calcsize
import argparse


class A5Pack:
    HDR_FMT = "<6s3s82x"
    HDR_SIZE = calcsize(HDR_FMT)
    INFO_CHUNK_FMT = "<20s20sI"
    INFO_CHUNK_SIZE = calcsize(INFO_CHUNK_FMT)

    def __init__(self, buf):
        self.buf = buf
        return

    def read_header(self):
        """returns tuple: signature and model id"""
        return unpack(A5Pack.HDR_FMT, self.buf[:A5Pack.HDR_SIZE])

    def get_first_file(self):
        self.offs_next_info_chunk = A5Pack.HDR_SIZE
        return self._get_file()

    def get_next_file(self):
        return self._get_file()

    def extract_file(self, offs, size):
        return self.buf[offs:offs+size]

    def _get_file(self):
        try:
            ver, tag, size = self._read_entry(self.offs_next_info_chunk)
        except ValueError:
            return None
            
        offs = self.offs_next_info_chunk + A5Pack.INFO_CHUNK_SIZE
        self.offs_next_info_chunk = offs + size
        return ver, tag, offs, size

    def _read_entry(self, offs):
        """returns tuple: ver, tag, size"""
        if len(self.buf) < offs+A5Pack.INFO_CHUNK_SIZE:
            raise ValueError()
        return unpack(A5Pack.INFO_CHUNK_FMT, self.buf[offs:offs+A5Pack.INFO_CHUNK_SIZE] )

parser = argparse.ArgumentParser()
parser.add_argument("filename", type=str, help="filename: A5Pack archive")

args = parser.parse_args()

f = open(args.filename, "rb")
buf = f.read()
f.close()

a5 = A5Pack(buf)
r = a5.get_first_file()
if r:
    file_idx = 0
    ver, tag, offs, size = r
    name = "%s_%d_%08x_%s" % (ver.decode("utf-8").strip("\x00"),
                            file_idx,
                            offs,
                            tag.decode("utf-8").strip("\x00").replace(" ", "_"))
    print("%s 0x%x %d" % (name, offs, size))
    f = open(name, "wb")
    f.write(a5.extract_file(offs, size))
    f.close()
    while True:
        r = a5.get_next_file()
        if r:
            file_idx += 1
            ver, tag, offs, size = r
            name = "%s_%d_%08x_%s" % (ver.decode("utf-8").strip("\x00"),
                                    file_idx,
                                    offs,
                                    tag.decode("utf-8").strip("\x00").replace(" ", "_"))
            print("%s 0x%x %d" % (name, offs, size))
            f = open(name, "wb")
            f.write(a5.extract_file(offs, size))
            f.close()
        else:
            print("No more files. %d files in total." % (file_idx+1))
            break