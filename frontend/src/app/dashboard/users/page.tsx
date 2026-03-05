'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  Users,
  Plus,
  Pencil,
  UserX,
  UserCheck,
  Search,
  ChevronLeft,
  ChevronRight,
  X,
  ShieldAlert,
  Loader2,
  Trash2,
} from 'lucide-react';
import Link from 'next/link';
import { useAuthStore } from '@/store';
import { usersService } from '@/services/usersService';
import { UserRole } from '@/types';
import type { UserDetail, CreateUserData, UpdateUserData } from '@/types';

// ── Constants ─────────────────────────────────────────────────────────────────

const ROLE_LABELS: Record<UserRole, string> = {
  [UserRole.CIUDADANO]: 'Ciudadano',
  [UserRole.BRIGADA]: 'Brigada',
  [UserRole.SUPERVISOR]: 'Supervisor',
  [UserRole.ADMIN]: 'Admin',
};

const ROLE_COLORS: Record<UserRole, string> = {
  [UserRole.CIUDADANO]: 'bg-gray-100 text-gray-700',
  [UserRole.BRIGADA]: 'bg-blue-100 text-blue-700',
  [UserRole.SUPERVISOR]: 'bg-violet-100 text-violet-700',
  [UserRole.ADMIN]: 'bg-red-100 text-red-700',
};

const ALL_ROLES = Object.values(UserRole);

// ── Modal ─────────────────────────────────────────────────────────────────────

interface ModalState {
  open: boolean;
  mode: 'create' | 'edit';
  target: UserDetail | null;
}

const EMPTY_FORM = {
  email: '',
  username: '',
  full_name: '',
  phone: '',
  role: UserRole.CIUDADANO,
  password: '',
  is_active: true,
};

function UserFormModal({
  state,
  onClose,
  onSaved,
}: {
  state: ModalState;
  onClose: () => void;
  onSaved: () => void;
}) {
  const isEdit = state.mode === 'edit';
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (state.open) {
      if (isEdit && state.target) {
        setForm({
          email: state.target.email,
          username: state.target.username,
          full_name: state.target.full_name ?? '',
          phone: state.target.phone ?? '',
          role: state.target.role,
          password: '',
          is_active: state.target.is_active,
        });
      } else {
        setForm({ ...EMPTY_FORM });
      }
      setError(null);
    }
  }, [state.open, isEdit, state.target]);

  const set = (field: keyof typeof form, value: string | boolean) =>
    setForm((f) => ({ ...f, [field]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (isEdit && state.target) {
        const payload: UpdateUserData = {
          email: form.email || undefined,
          username: form.username || undefined,
          full_name: form.full_name || undefined,
          phone: form.phone || undefined,
          role: form.role,
          is_active: form.is_active,
        };
        if (form.password) payload.password = form.password;
        await usersService.updateUser(state.target.id, payload);
      } else {
        const payload: CreateUserData = {
          email: form.email,
          username: form.username,
          full_name: form.full_name || undefined,
          phone: form.phone || undefined,
          role: form.role,
          password: form.password,
        };
        await usersService.createUser(payload);
      }
      onSaved();
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? err.message ?? 'Error al guardar');
    } finally {
      setLoading(false);
    }
  };

  if (!state.open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-lg bg-white rounded-xl shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">
            {isEdit ? 'Editar usuario' : 'Nuevo usuario'}
          </h2>
          <button onClick={onClose} className="p-1.5 rounded hover:bg-gray-100">
            <X className="w-4 h-4 text-gray-500" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-3 py-2 text-sm">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-gray-600 block mb-1">
                Username <span className="text-red-500">*</span>
              </label>
              <input
                required
                value={form.username}
                onChange={(e) => set('username', e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="juanperez"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-600 block mb-1">
                Nombre completo
              </label>
              <input
                value={form.full_name}
                onChange={(e) => set('full_name', e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Juan Pérez"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">
              Email <span className="text-red-500">*</span>
            </label>
            <input
              required
              type="email"
              value={form.email}
              onChange={(e) => set('email', e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="correo@ejemplo.com"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-gray-600 block mb-1">Teléfono</label>
              <input
                value={form.phone}
                onChange={(e) => set('phone', e.target.value)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="+1809-555-0100"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-600 block mb-1">
                Rol <span className="text-red-500">*</span>
              </label>
              <select
                value={form.role}
                onChange={(e) => set('role', e.target.value as UserRole)}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              >
                {ALL_ROLES.map((r) => (
                  <option key={r} value={r}>
                    {ROLE_LABELS[r]}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-gray-600 block mb-1">
              Contraseña {!isEdit && <span className="text-red-500">*</span>}
              {isEdit && (
                <span className="text-gray-400 font-normal"> (dejar en blanco para no cambiar)</span>
              )}
            </label>
            <input
              required={!isEdit}
              type="password"
              value={form.password}
              onChange={(e) => set('password', e.target.value)}
              minLength={8}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Mínimo 8 caracteres"
            />
          </div>

          {isEdit && (
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(e) => set('is_active', e.target.checked)}
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Usuario activo</span>
            </label>
          )}

          {/* Footer */}
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {loading && <Loader2 className="w-3 h-3 animate-spin" />}
              {isEdit ? 'Guardar cambios' : 'Crear usuario'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function UsersPage() {
  const { user: me, setUser } = useAuthStore();
  // Sync role from backend on mount — covers the case where localStorage has
  // a stale role (e.g. role was changed on the server after last login).
  const [roleLoaded, setRoleLoaded] = useState(false);
  useEffect(() => {
    usersService.getMe().then((profile) => {
      if (me) {
        setUser({ ...me, role: profile.role });
      }
    }).catch((err) => {
      console.error('[UsersPage] getMe failed:', err);
    }).finally(() => setRoleLoaded(true));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const isAdmin = me?.role === UserRole.ADMIN;

  // Data state
  const [users, setUsers] = useState<UserDetail[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [activeFilter, setActiveFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const PER_PAGE = 15;

  // Modal state
  const [modal, setModal] = useState<ModalState>({ open: false, mode: 'create', target: null });

  // Action loading per row
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);

  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const is_active =
        activeFilter === 'true' ? true : activeFilter === 'false' ? false : undefined;
      const result = await usersService.listUsers({
        page,
        per_page: PER_PAGE,
        search: search || undefined,
        role: roleFilter || undefined,
        is_active,
      });
      setUsers(result.users);
      setTotal(result.total);
      setTotalPages(result.total_pages);
    } catch {
      setError('No se pudieron cargar los usuarios');
    } finally {
      setLoading(false);
    }
  }, [page, search, roleFilter, activeFilter]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [search, roleFilter, activeFilter]);

  const handleToggleActive = async (u: UserDetail) => {
    setActionLoading(u.id);
    try {
      if (u.is_active) {
        await usersService.deactivateUser(u.id);
        showToast(`${u.username} desactivado`);
      } else {
        await usersService.updateUser(u.id, { is_active: true });
        showToast(`${u.username} activado`);
      }
      fetchUsers();
    } catch (err: any) {
      showToast(err?.response?.data?.detail ?? err?.detail ?? 'Error al actualizar estado', false);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (u: UserDetail) => {
    if (!confirm(`¿Estás seguro de eliminar permanentemente a "${u.username}"? Esta acción no se puede deshacer.`)) return;
    setActionLoading(u.id);
    try {
      await usersService.deleteUser(u.id);
      showToast(`${u.username} eliminado permanentemente`);
      fetchUsers();
    } catch (err: any) {
      showToast(err?.response?.data?.detail ?? err?.detail ?? 'Error al eliminar usuario', false);
    } finally {
      setActionLoading(null);
    }
  };

  const handleModalSaved = () => {
    setModal({ open: false, mode: 'create', target: null });
    showToast(modal.mode === 'create' ? 'Usuario creado' : 'Usuario actualizado');
    fetchUsers();
  };

  const fmtDate = (s: string | null) =>
    s ? new Date(s).toLocaleDateString('es-DO', { day: '2-digit', month: 'short', year: 'numeric' }) : '—';

  return (
    <div className="space-y-5">
      {/* Toast */}
      {toast && (
        <div
          className={`fixed bottom-5 right-5 z-50 px-4 py-3 rounded-lg text-sm font-medium shadow-lg transition-all
            ${toast.ok ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}
        >
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="p-1.5 rounded-md hover:bg-gray-100 transition-colors"
          >
            <ChevronLeft className="h-5 w-5 text-gray-500" />
          </Link>
          <div className="p-2 bg-violet-100 rounded-lg">
            <Users className="w-5 h-5 text-violet-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Gestión de Usuarios</h1>
            <p className="text-sm text-gray-500">
              {total} usuario{total !== 1 ? 's' : ''} en el sistema
            </p>
          </div>
        </div>
        {isAdmin && (
          <button
            onClick={() => setModal({ open: true, mode: 'create', target: null })}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nuevo usuario
          </button>
        )}
      </div>

      {/* Permission notice for non-admins */}
      {!isAdmin && (
        <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 text-amber-700 rounded-lg px-4 py-2 text-sm">
          <ShieldAlert className="w-4 h-4 flex-shrink-0" />
          Vista de solo lectura. Solo los administradores pueden crear o editar usuarios.
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por nombre, email o username…"
            className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todos los roles</option>
          {ALL_ROLES.map((r) => (
            <option key={r} value={r}>
              {ROLE_LABELS[r]}
            </option>
          ))}
        </select>

        <select
          value={activeFilter}
          onChange={(e) => setActiveFilter(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Activos e inactivos</option>
          <option value="true">Solo activos</option>
          <option value="false">Solo inactivos</option>
        </select>
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                {['ID', 'Usuario', 'Email', 'Rol', 'Estado', 'Verificado', 'Creado', 'Último acceso', 'Acciones'].map(
                  (h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
                    >
                      {h}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loading ? (
                <tr>
                  <td colSpan={9} className="px-4 py-12 text-center text-gray-400">
                    <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
                    Cargando usuarios…
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-12 text-center text-gray-400">
                    No se encontraron usuarios con los filtros aplicados.
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr
                    key={u.id}
                    className={`hover:bg-gray-50 transition-colors ${!u.is_active ? 'opacity-60' : ''}`}
                  >
                    <td className="px-4 py-3 text-gray-400 font-mono text-xs">{u.id}</td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">{u.username}</div>
                      {u.full_name && (
                        <div className="text-xs text-gray-400">{u.full_name}</div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{u.email}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${ROLE_COLORS[u.role]}`}
                      >
                        {ROLE_LABELS[u.role]}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          u.is_active
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-500'
                        }`}
                      >
                        {u.is_active ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {u.is_verified ? (
                        <span className="text-green-500 text-xs">✓</span>
                      ) : (
                        <span className="text-gray-300 text-xs">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                      {fmtDate(u.created_at)}
                    </td>
                    <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                      {fmtDate(u.last_login)}
                    </td>
                    <td className="px-4 py-3">
                      {isAdmin && (
                        <div className="flex items-center gap-1">
                          <button
                            title="Editar"
                            onClick={() => setModal({ open: true, mode: 'edit', target: u })}
                            className="p-1.5 rounded hover:bg-blue-50 text-blue-600 transition-colors"
                          >
                            <Pencil className="w-3.5 h-3.5" />
                          </button>
                          <button
                            title={u.is_active ? 'Desactivar' : 'Activar'}
                            disabled={actionLoading === u.id || u.id === me?.id}
                            onClick={() => handleToggleActive(u)}
                            className={`p-1.5 rounded transition-colors disabled:opacity-40 ${
                              u.is_active
                                ? 'hover:bg-red-50 text-red-500'
                                : 'hover:bg-green-50 text-green-600'
                            }`}
                          >
                            {actionLoading === u.id ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : u.is_active ? (
                              <UserX className="w-3.5 h-3.5" />
                            ) : (
                              <UserCheck className="w-3.5 h-3.5" />
                            )}
                          </button>
                          <button
                            title="Eliminar permanentemente"
                            disabled={actionLoading === u.id || u.id === me?.id}
                            onClick={() => handleDelete(u)}
                            className="p-1.5 rounded hover:bg-red-50 text-red-400 hover:text-red-600 transition-colors disabled:opacity-40"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 bg-gray-50">
            <p className="text-xs text-gray-500">
              Mostrando {(page - 1) * PER_PAGE + 1}–{Math.min(page * PER_PAGE, total)} de {total}
            </p>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-1.5 rounded hover:bg-white border border-gray-200 disabled:opacity-40 transition-colors"
              >
                <ChevronLeft className="w-3.5 h-3.5 text-gray-600" />
              </button>
              <span className="px-3 py-1 text-xs text-gray-600 font-medium">
                {page} / {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-1.5 rounded hover:bg-white border border-gray-200 disabled:opacity-40 transition-colors"
              >
                <ChevronRight className="w-3.5 h-3.5 text-gray-600" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modal */}
      <UserFormModal state={modal} onClose={() => setModal({ ...modal, open: false })} onSaved={handleModalSaved} />
    </div>
  );
}
