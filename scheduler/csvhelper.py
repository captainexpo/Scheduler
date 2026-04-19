class CSVWriter:
    def __init__(self):
        self.header = []
        self.lines = []
        self.curline = []

    def write(self, value):
        self.curline.append(str(value))

    def escape_line(self, line):
        escaped_line = []
        for item in line:
            if isinstance(item, str):
                if ',' in item or '"' in item:
                    item = item.replace('"', '""')
                    escaped_line.append(f'"{item}"')
                else:
                    escaped_line.append(item)
            else:
                escaped_line.append(str(item))
        return escaped_line

    def flush_line(self):
        if self.curline:
            self.lines.append(','.join(self.escape_line(self.curline)) + '\n')
            self.curline = []

    def get_raw_data(self):
        o = ""
        if self.header:
            o += self.header + '\n'
        for line in self.lines:
            o += line
        return o

    def save(self, filename):
        with open(filename, 'w') as file:
            if self.header:
                self.write_header(self.header)
            for line in self.lines:
                self.write_line(line)

    def write_line(self, line):
        escaped_line = self.escape_line(line)
        self.lines.append(','.join(escaped_line) + '\n')

    def write_header(self, header: str):
        self.header = header
