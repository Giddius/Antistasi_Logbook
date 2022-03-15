

cdef class RecordLine:
    cdef readonly str content
    cdef readonly unsigned long start

    def __cinit__(self, content, start):
        self.content = content
        self.start = start

    def __repr__(self):
        return self.content

    def __str__(self) -> str:
        return self.content
