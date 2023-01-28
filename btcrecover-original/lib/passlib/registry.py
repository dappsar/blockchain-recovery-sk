"""passlib.registry - registry for password hash handlers"""
#=============================================================================
# imports
#=============================================================================
# core
import re
import logging; log = logging.getLogger(__name__)
from warnings import warn
# pkg
from lib.passlib import exc
from lib.passlib.exc import ExpectedTypeError, PasslibWarning
from lib.passlib.ifc import PasswordHash
from lib.passlib.utils import (
    is_crypt_handler, has_crypt as os_crypt_present,
    unix_crypt_schemes as os_crypt_schemes,
)
from lib.passlib.utils.compat import unicode_or_str
from lib.passlib.utils.decor import memoize_single_value
# local
__all__ = [
    "register_crypt_handler_path",
    "register_crypt_handler",
    "get_crypt_handler",
    "list_crypt_handlers",
]

#=============================================================================
# proxy object used in place of 'passlib.hash' module
#=============================================================================
class _PasslibRegistryProxy(object):
    """proxy module passlib.hash

    this module is in fact an object which lazy-loads
    the requested password hash algorithm from wherever it has been stored.
    it acts as a thin wrapper around :func:`passlib.registry.get_crypt_handler`.
    """
    __name__ = "passlib.hash"
    __package__ = None

    def __getattr__(self, attr):
        if attr.startswith("_"):
            raise AttributeError("missing attribute: %r" % (attr,))
        handler = get_crypt_handler(attr, None)
        if handler:
            return handler
        else:
            raise AttributeError("unknown password hash: %r" % (attr,))

    def __setattr__(self, attr, value):
        if attr.startswith("_"):
            # writing to private attributes should behave normally.
            # (required so GAE can write to the __loader__ attribute).
            object.__setattr__(self, attr, value)
        else:
            # writing to public attributes should be treated
            # as attempting to register a handler.
            register_crypt_handler(value, _attr=attr)

    def __repr__(self):
        return "<proxy module 'passlib.hash'>"

    def __dir__(self):
        # this adds in lazy-loaded handler names,
        # otherwise this is the standard dir() implementation.
        attrs = set(dir(self.__class__))
        attrs.update(self.__dict__)
        attrs.update(_locations)
        return sorted(attrs)

# create single instance - available publically as 'passlib.hash'
_proxy = _PasslibRegistryProxy()

#=============================================================================
# internal registry state
#=============================================================================

# singleton uses to detect omitted keywords
_UNSET = object()

# dict mapping name -> loaded handlers (just uses proxy object's internal dict)
_handlers = _proxy.__dict__

# dict mapping names -> import path for lazy loading.
#     * import path should be "module.path" or "module.path:attr"
#     * if attr omitted, "name" used as default.
_locations = dict(
    # NOTE: this is a hardcoded list of the handlers built into passlib,
    #       applications should call register_crypt_handler_path()
    apr_md5_crypt = "passlib.handlers.md5_crypt",
    argon2 = "passlib.handlers.argon2",
    atlassian_pbkdf2_sha1 = "passlib.handlers.pbkdf2",
    bcrypt = "passlib.handlers.bcrypt",
    bcrypt_sha256 = "passlib.handlers.bcrypt",
    bigcrypt = "passlib.handlers.des_crypt",
    bsd_nthash = "passlib.handlers.windows",
    bsdi_crypt = "passlib.handlers.des_crypt",
    cisco_pix = "passlib.handlers.cisco",
    cisco_asa = "passlib.handlers.cisco",
    cisco_type7 = "passlib.handlers.cisco",
    cta_pbkdf2_sha1 = "passlib.handlers.pbkdf2",
    crypt16 = "passlib.handlers.des_crypt",
    des_crypt = "passlib.handlers.des_crypt",
    django_argon2 = "passlib.handlers.django",
    django_bcrypt = "passlib.handlers.django",
    django_bcrypt_sha256 = "passlib.handlers.django",
    django_pbkdf2_sha256 = "passlib.handlers.django",
    django_pbkdf2_sha1 = "passlib.handlers.django",
    django_salted_sha1 = "passlib.handlers.django",
    django_salted_md5 = "passlib.handlers.django",
    django_des_crypt = "passlib.handlers.django",
    django_disabled = "passlib.handlers.django",
    dlitz_pbkdf2_sha1 = "passlib.handlers.pbkdf2",
    fshp = "passlib.handlers.fshp",
    grub_pbkdf2_sha512 = "passlib.handlers.pbkdf2",
    hex_md4 = "passlib.handlers.digests",
    hex_md5 = "passlib.handlers.digests",
    hex_sha1 = "passlib.handlers.digests",
    hex_sha256 = "passlib.handlers.digests",
    hex_sha512 = "passlib.handlers.digests",
    htdigest = "passlib.handlers.digests",
    ldap_plaintext = "passlib.handlers.ldap_digests",
    ldap_md5 = "passlib.handlers.ldap_digests",
    ldap_sha1 = "passlib.handlers.ldap_digests",
    ldap_hex_md5 = "passlib.handlers.roundup",
    ldap_hex_sha1 = "passlib.handlers.roundup",
    ldap_salted_md5 = "passlib.handlers.ldap_digests",
    ldap_salted_sha1 = "passlib.handlers.ldap_digests",
    ldap_des_crypt = "passlib.handlers.ldap_digests",
    ldap_bsdi_crypt = "passlib.handlers.ldap_digests",
    ldap_md5_crypt = "passlib.handlers.ldap_digests",
    ldap_bcrypt = "passlib.handlers.ldap_digests",
    ldap_sha1_crypt = "passlib.handlers.ldap_digests",
    ldap_sha256_crypt = "passlib.handlers.ldap_digests",
    ldap_sha512_crypt = "passlib.handlers.ldap_digests",
    ldap_pbkdf2_sha1 = "passlib.handlers.pbkdf2",
    ldap_pbkdf2_sha256 = "passlib.handlers.pbkdf2",
    ldap_pbkdf2_sha512 = "passlib.handlers.pbkdf2",
    lmhash = "passlib.handlers.windows",
    md5_crypt = "passlib.handlers.md5_crypt",
    msdcc = "passlib.handlers.windows",
    msdcc2 = "passlib.handlers.windows",
    mssql2000 = "passlib.handlers.mssql",
    mssql2005 = "passlib.handlers.mssql",
    mysql323 = "passlib.handlers.mysql",
    mysql41 = "passlib.handlers.mysql",
    nthash = "passlib.handlers.windows",
    oracle10 = "passlib.handlers.oracle",
    oracle11 = "passlib.handlers.oracle",
    pbkdf2_sha1 = "passlib.handlers.pbkdf2",
    pbkdf2_sha256 = "passlib.handlers.pbkdf2",
    pbkdf2_sha512 = "passlib.handlers.pbkdf2",
    phpass = "passlib.handlers.phpass",
    plaintext = "passlib.handlers.misc",
    postgres_md5 = "passlib.handlers.postgres",
    roundup_plaintext = "passlib.handlers.roundup",
    scram = "passlib.handlers.scram",
    scrypt = "passlib.handlers.scrypt",
    sha1_crypt = "passlib.handlers.sha1_crypt",
    sha256_crypt = "passlib.handlers.sha2_crypt",
    sha512_crypt = "passlib.handlers.sha2_crypt",
    sun_md5_crypt = "passlib.handlers.sun_md5_crypt",
    unix_disabled = "passlib.handlers.misc",
    unix_fallback = "passlib.handlers.misc",
)

# master regexp for detecting valid handler names
_name_re = re.compile("^[a-z][a-z0-9_]+[a-z0-9]$")

# names which aren't allowed for various reasons
# (mainly keyword conflicts in CryptContext)
_forbidden_names = frozenset(["onload", "policy", "context", "all",
                              "default", "none", "auto"])

#=============================================================================
# registry frontend functions
#=============================================================================
def _validate_handler_name(name):
    """helper to validate handler name

    :raises ValueError:
        * if empty name
        * if name not lower case
        * if name contains double underscores
        * if name is reserved (e.g. ``context``, ``all``).
    """
    if not name:
        raise ValueError("handler name cannot be empty: %r" % (name,))
    if name.lower() != name:
        raise ValueError("name must be lower-case: %r" % (name,))
    if not _name_re.match(name):
        raise ValueError("invalid name (must be 3+ characters, "
                         " begin with a-z, and contain only underscore, a-z, "
                         "0-9): %r" % (name,))
    if '__' in name:
        raise ValueError("name may not contain double-underscores: %r" %
                         (name,))
    if name in _forbidden_names:
        raise ValueError("that name is not allowed: %r" % (name,))
    return True

def register_crypt_handler_path(name, path):
    """register location to lazy-load handler when requested.

    custom hashes may be registered via :func:`register_crypt_handler`,
    or they may be registered by this function,
    which will delay actually importing and loading the handler
    until a call to :func:`get_crypt_handler` is made for the specified name.

    :arg name: name of handler
    :arg path: module import path

    the specified module path should contain a password hash handler
    called :samp:`{name}`, or the path may contain a colon,
    specifying the module and module attribute to use.
    for example, the following would cause ``get_handler("myhash")`` to look
    for a class named ``myhash`` within the ``myapp.helpers`` module::

        >>> from passlib.registry import registry_crypt_handler_path
        >>> registry_crypt_handler_path("myhash", "myapp.helpers")

    ...while this form would cause ``get_handler("myhash")`` to look
    for a class name ``MyHash`` within the ``myapp.helpers`` module::

        >>> from passlib.registry import registry_crypt_handler_path
        >>> registry_crypt_handler_path("myhash", "myapp.helpers:MyHash")
    """
    # validate name
    _validate_handler_name(name)

    # validate path
    if path.startswith("."):
        raise ValueError("path cannot start with '.'")
    if ':' in path:
        if path.count(':') > 1:
            raise ValueError("path cannot have more than one ':'")
        if path.find('.', path.index(':')) > -1:
            raise ValueError("path cannot have '.' to right of ':'")

    # store location
    _locations[name] = path
    log.debug("registered path to %r handler: %r", name, path)

def register_crypt_handler(handler, force=False, _attr=None):
    """register password hash handler.

    this method immediately registers a handler with the internal passlib registry,
    so that it will be returned by :func:`get_crypt_handler` when requested.

    :arg handler: the password hash handler to register
    :param force: force override of existing handler (defaults to False)
    :param _attr:
        [internal kwd] if specified, ensures ``handler.name``
        matches this value, or raises :exc:`ValueError`.

    :raises TypeError:
        if the specified object does not appear to be a valid handler.

    :raises ValueError:
        if the specified object's name (or other required attributes)
        contain invalid values.

    :raises KeyError:
        if a (different) handler was already registered with
        the same name, and ``force=True`` was not specified.
    """
    # validate handler
    if not is_crypt_handler(handler):
        raise ExpectedTypeError(handler, "password hash handler", "handler")
    if not handler:
        raise AssertionError("``bool(handler)`` must be True")

    # validate name
    name = handler.name
    _validate_handler_name(name)
    if _attr and _attr != name:
        raise ValueError("handlers must be stored only under their own name (%r != %r)" %
                         (_attr, name))

    # check for existing handler
    other = _handlers.get(name)
    if other:
        if other is handler:
            log.debug("same %r handler already registered: %r", name, handler)
            return
        elif force:
            log.warning("overriding previously registered %r handler: %r",
                        name, other)
        else:
            raise KeyError("another %r handler has already been registered: %r" %
                           (name, other))

    # register handler
    _handlers[name] = handler
    log.debug("registered %r handler: %r", name, handler)

def get_crypt_handler(name, default=_UNSET):
    """return handler for specified password hash scheme.

    this method looks up a handler for the specified scheme.
    if the handler is not already loaded,
    it checks if the location is known, and loads it first.

    :arg name: name of handler to return
    :param default: optional default value to return if no handler with specified name is found.

    :raises KeyError: if no handler matching that name is found, and no default specified, a KeyError will be raised.

    :returns: handler attached to name, or default value (if specified).
    """
    # catch invalid names before we check _handlers,
    # since it's a module dict, and exposes things like __package__, etc.
    if name.startswith("_"):
        if default is _UNSET:
            raise KeyError("invalid handler name: %r" % (name,))
        else:
            return default

    # check if handler is already loaded
    try:
        return _handlers[name]
    except KeyError:
        pass

    # normalize name (and if changed, check dict again)
    assert isinstance(name, unicode_or_str), "name must be string instance"
    alt = name.replace("-","_").lower()
    if alt != name:
        warn("handler names should be lower-case, and use underscores instead "
             "of hyphens: %r => %r" % (name, alt), PasslibWarning,
             stacklevel=2)
        name = alt

        # try to load using new name
        try:
            return _handlers[name]
        except KeyError:
            pass

    # check if lazy load mapping has been specified for this driver
    path = _locations.get(name)
    if path:
        if ':' in path:
            modname, modattr = path.split(":")
        else:
            modname, modattr = path, name
        ##log.debug("loading %r handler from path: '%s:%s'", name, modname, modattr)

        # try to load the module - any import errors indicate runtime config, usually
        # either missing package, or bad path provided to register_crypt_handler_path()
        mod = __import__(modname, fromlist=[modattr], level=0)

        # first check if importing module triggered register_crypt_handler(),
        # (this is discouraged due to its magical implicitness)
        handler = _handlers.get(name)
        if handler:
            # XXX: issue deprecation warning here?
            assert is_crypt_handler(handler), "unexpected object: name=%r object=%r" % (name, handler)
            return handler

        # then get real handler & register it
        handler = getattr(mod, modattr)
        register_crypt_handler(handler, _attr=name)
        return handler

    # fail!
    if default is _UNSET:
        raise KeyError("no crypt handler found for algorithm: %r" % (name,))
    else:
        return default

def list_crypt_handlers(loaded_only=False):
    """return sorted list of all known crypt handler names.

    :param loaded_only: if ``True``, only returns names of handlers which have actually been loaded.

    :returns: list of names of all known handlers
    """
    names = set(_handlers)
    if not loaded_only:
        names.update(_locations)
    # strip private attrs out of namespace and sort.
    # TODO: make _handlers a separate list, so we don't have module namespace mixed in.
    return sorted(name for name in names if not name.startswith("_"))

# NOTE: these two functions mainly exist just for the unittests...

def _has_crypt_handler(name, loaded_only=False):
    """check if handler name is known.

    this is only useful for two cases:

    * quickly checking if handler has already been loaded
    * checking if handler exists, without actually loading it

    :arg name: name of handler
    :param loaded_only: if ``True``, returns False if handler exists but hasn't been loaded
    """
    return (name in _handlers) or (not loaded_only and name in _locations)

def _unload_handler_name(name, locations=True):
    """unloads a handler from the registry.

    .. warning::

        this is an internal function,
        used only by the unittests.

    if loaded handler is found with specified name, it's removed.
    if path to lazy load handler is found, it's removed.

    missing names are a noop.

    :arg name: name of handler to unload
    :param locations: if False, won't purge registered handler locations (default True)
    """
    if name in _handlers:
        del _handlers[name]
    if locations and name in _locations:
        del _locations[name]

#=============================================================================
# inspection helpers
#=============================================================================

#------------------------------------------------------------------
# general
#------------------------------------------------------------------

# TODO: needs UTs
def _resolve(hasher, param="value"):
    """
    internal helper to resolve argument to hasher object
    """
    if is_crypt_handler(hasher):
        return hasher
    elif isinstance(hasher, unicode_or_str):
        return get_crypt_handler(hasher)
    else:
        raise exc.ExpectedTypeError(hasher, unicode_or_str, param)


#: backend aliases
ANY = "any"
BUILTIN = "builtin"
OS_CRYPT = "os_crypt"

# TODO: needs UTs
def has_backend(hasher, backend=ANY, safe=False):
    """
    Test if specified backend is available for hasher.

    :param hasher:
        Hasher name or object.

    :param backend:
        Name of backend, or ``"any"`` if any backend will do.
        For hashers without multiple backends, will pretend
        they have a single backend named ``"builtin"``.

    :param safe:
        By default, throws error if backend is unknown.
        If ``safe=True``, will just return false value.

    :raises ValueError:
        * if hasher name is unknown.
        * if backend is unknown to hasher, and safe=False.

    :return:
        True if backend available, False if not available,
        and None if unknown + safe=True.
    """
    hasher = _resolve(hasher)

    if backend == ANY:
        if not hasattr(hasher, "get_backend"):
            # single backend, assume it's loaded
            return True

        # multiple backends, check at least one is loadable
        try:
            hasher.get_backend()
            return True
        except exc.MissingBackendError:
            return False

    # test for specific backend
    if hasattr(hasher, "has_backend"):
        # multiple backends
        if safe and backend not in hasher.backends:
            return None
        return hasher.has_backend(backend)

    # single builtin backend
    if backend == BUILTIN:
        return True
    elif safe:
        return None
    else:
        raise exc.UnknownBackendError(hasher, backend)

#------------------------------------------------------------------
# os crypt
#------------------------------------------------------------------

# TODO: move unix_crypt_schemes list to here.
# os_crypt_schemes -- alias for unix_crypt_schemes above


# TODO: needs UTs
@memoize_single_value
def get_supported_os_crypt_schemes():
    """
    return tuple of schemes which :func:`crypt.crypt` natively supports.
    """
    if not os_crypt_present:
        return ()
    cache = tuple(name for name in os_crypt_schemes
                  if get_crypt_handler(name).has_backend(OS_CRYPT))
    if not cache:  # pragma: no cover -- sanity check
        # no idea what OS this could happen on...
        warn("crypt.crypt() function is present, but doesn't support any "
             "formats known to passlib!", exc.PasslibRuntimeWarning)
    return cache


# TODO: needs UTs
def has_os_crypt_support(hasher):
    """
    check if hash is supported by native :func:`crypt.crypt` function.
    if :func:`crypt.crypt` is not present, will always return False.

    :param hasher:
        name or hasher object.

    :returns bool:
        True if hash format is supported by OS, else False.
    """
    return os_crypt_present and has_backend(hasher, OS_CRYPT, safe=True)

#=============================================================================
# eof
#=============================================================================
