from collections import defaultdict
import operator


class EventHandler(object):
    def __init__(self):
        self._data = defaultdict(list)

    def push(self, event, *args):
        for obj, action in self._data[event]:
            getattr(obj, action)(*args)

    def register(self, event, obj, action):
        self._data[event].append([obj, action])


EventHandler = EventHandler()


class Empty(object):
    __slots__ = ()

    def __getitem__(self, k):
        raise KeyError('"%s" key not found eventually' % k)


Empty = Empty()


class datadict(object):
    _dispatcher = EventHandler
    _proto = Empty

    def __new__(cls, *args, **kwargs):
        self = object.__new__(cls)
        self._data = dict()
        return self

    def __init__(self, *args, **kwargs):
        for i in args:
            self.update(i)
        self.update(kwargs)

    def update(self, v):
        if hasattr(v, "_data"):
            self._data.update(v._data)
        elif hasattr(v, "items"):
            self._data.update(v)
        elif hasattr(v, "__dict__"):
            self._data.update(v.__dict__)
        else:
            self._data.update(v)

    def __getitem__(self, k):
        try:
            v = self._data[k]
        except KeyError:
            v = self._proto[k]
        if hasattr(v, "_autocall"):
            return v._autocall(self, k)
        else:
            return v

    def get(self, k, default=None):
        try:
            return self[k]
        except KeyError:
            return default

    def __iter__(self):
        for i in list(self.keys()):
            yield i

    def items(self):
        for k in list(self.keys()):
            yield k, self[k]

    def __setitem__(self, k, v):
        self._data[k] = v
        if hasattr(v, "_autoset"):
            v._autoset(self, k)
        if self._dispatcher:
            self._dispatcher.push("changestate", self)

    def __delitem__(self, k):
        del self._data[k]
        if self._dispatcher:
            self._dispatcher.push("changestate", self)

    def keys(self):
        return list(self._data.keys())

    def setdefault(self, k, d=None):
        return self._data.setdefault(k, d)

    def __contains__(self, k):
        return k in self._data

    def _set_events(s):
        if s:
            self._dispatcher = EventHandler
        else:
            self._dispatcher = None

    def __repr__(self):
        """long representation"""
        attrs = [k for k in list(self._data.keys()) if not k.startswith("_")]
        name = " %s" % id(self)
        if self._proto is not Empty:
            proto = "_proto=%s" % self._proto
        else:
            proto = ""
        out = ["<%s%s%s" % (self.__class__.__name__, name, proto)]
        for k in sorted(attrs):
            v = self._show(k)
            if hasattr(v, "shape"):
                v = "<array %s%s>" % (v.dtype.name, list(v.shape))
            out.append("  %-25s = %s" % (k, v))
        out[-1] = out[-1] + " >"
        if len(out) > 120:
            out = out[:15] + ["  ..."] + out[-15:]
        return "\n".join(out)

    def __str__(self):
        """short representation"""
        if "name" in self._data:
            name = ' "%s"' % self["name"]
        else:
            name = " %s" % id(self)
        return "<%s%s>" % (self.__class__.__name__, name)

    def _show(self, k):
        return self._data[k]

    def __call__(self, k):
        return eval(k, {}, self)


class dataobj(datadict):
    __dict__ = property(operator.attrgetter("_data"))

    def __getattribute__(self, k):
        if k.startswith("_"):
            return object.__getattribute__(self, k)
        else:
            try:
                return self[k]
            except KeyError:
                return object.__getattribute__(self, k)

    def __setattr__(self, k, v):
        if k.startswith("_"):
            object.__setattr__(self, k, v)
        else:
            self[k] = v

    def __delattr__(self, k):
        if k.startswith("_"):
            object.__delattr__(self, k)
        else:
            del self[k]
