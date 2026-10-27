// Weapon reloads - the V3 experiment (D132; a "nice to have", D121).
//
// Doom has no magazines: a gun fires until its ammo pool is empty. D47
// parked reloads so D39's balance would stand; D132 asked to explore them
// with NO NEW ART, as an option the CEO plays with and without. So:
//
//   * the CVar `sd_reloads` (CVARINFO; Options > Soviet Doom) turns the
//     whole mechanic on or off at any moment. Off, every gun behaves exactly
//     as in v1.2 (the IZh-58 keeps its own two-barrel break-open, which was
//     never optional);
//   * a MAGAZINE is a counter over the weapon's ammo pool, not a second
//     pool: firing still takes the round from the pool (Clip, Cell,
//     SD_AkmAmmo), and the magazine only says how many rounds may go before
//     the gun must be reloaded. No ammunition is created or lost, so the
//     maps' ammo (BALANCE.md section 8) is untouched;
//   * the reload has no frames of its own: the gun is lowered off screen
//     and raised again, as on a weapon switch, with the weapon's existing
//     reload sound (SNDINFO) while it is out of sight.
//
// Design, numbers and what to check in the engine:
// docs/engine/2026-10-25_V3_reloads.md; the decision: ADR 014; the DPS
// before and after: BALANCE.md section 10.
//
// A MIXIN CLASS is ZScript's way to share fields and functions between
// classes that do not share a base: `mixin SD_MagazineWeapon;` inside a
// class copies this body into it. The TT-33 (a Pistol), the PPSh-41 (a
// Chaingun), the AKM (a DoomWeapon) and the ROKS-3 (a PlasmaRifle) each
// include it. Every function takes the weapon's capacity as an argument,
// so nothing here depends on a name the including class must define.
// NOT VERIFIED in the engine (D26): that g4.14.2 accepts an `override` and
// `action` functions inside a mixin (the keyword is in gzdoom.exe; the
// engine's own gzdoom.pk3 uses no mixin to copy).

// Static helpers, callable from play (the weapons) and ui (the HUD readout).
// No scope keyword: a plain class's static functions are clearscope.
class SD_Reloads
{
	// The CVar (src/lumps/CVARINFO). Missing (a broken package), the mod
	// behaves as v1.2 did: no magazines.
	const SD_RELOADS_CVAR = "sd_reloads";

	// Where a weapon sprite rests and where it is out of sight, in psprite
	// y units: the engine's WEAPONTOP and WEAPONBOTTOM (gzdoom.pk3
	// constants.zs, 32 and 128), repeated so the numbers the tests read are
	// here.
	const SD_RELOAD_TOP = 32.0;
	const SD_RELOAD_BOTTOM = 128.0;

	static bool On()
	{
		CVar cv = CVar.FindCVar(SD_RELOADS_CVAR);
		return cv != null && cv.GetBool();
	}

	// The weapon sprite's y on tic `t` (1..total) of a reload: down over
	// `drop` tics, out of sight, up over the last `drop` tics. Tic `total`
	// is the rest position again.
	static double ReloadOffset(int t, int total, int drop)
	{
		if (drop <= 0 || t <= 0 || t >= total)
		{
			return SD_RELOAD_TOP;
		}
		double travel = SD_RELOAD_BOTTOM - SD_RELOAD_TOP;
		if (t < drop)
		{
			return SD_RELOAD_TOP + travel * t / drop;
		}
		if (t > total - drop)
		{
			return SD_RELOAD_TOP + travel * (total - t) / drop;
		}
		return SD_RELOAD_BOTTOM;
	}

	// (rounds loaded, capacity) of `w` for the HUD readout; capacity 0 for
	// a weapon with no magazine (the ice axe, the RPG-7, the Katyusha, the
	// RGD-5). The IZh-58 reports its barrels.
	static int, int Magazine(Weapon w)
	{
		let tt = SD_Tokarev(w);
		if (tt != null)
		{
			return tt.SD_MagazineLoaded(SD_Tokarev.SD_TT_MAGAZINE), SD_Tokarev.SD_TT_MAGAZINE;
		}
		let ppsh = SD_Ppsh(w);
		if (ppsh != null)
		{
			return ppsh.SD_MagazineLoaded(SD_Ppsh.SD_PPSH_MAGAZINE), SD_Ppsh.SD_PPSH_MAGAZINE;
		}
		let akm = SD_Akm(w);
		if (akm != null)
		{
			return akm.SD_MagazineLoaded(SD_Akm.SD_AKM_MAGAZINE), SD_Akm.SD_AKM_MAGAZINE;
		}
		let roks = SD_Roks3(w);
		if (roks != null)
		{
			return roks.SD_MagazineLoaded(SD_Roks3.SD_ROKS3_TANK), SD_Roks3.SD_ROKS3_TANK;
		}
		let izh = SD_Izh(w);
		if (izh != null)
		{
			int shells = izh.Ammo1 != null ? izh.Ammo1.Amount : 0;
			return min(izh.barrels, shells), SD_Izh.SD_IZH_BARRELS;
		}
		return 0, 0;
	}
}

mixin class SD_MagazineWeapon
{
	// Rounds fired since the magazine was last filled. 0 is a full
	// magazine, so a weapon is picked up, given at the start or read from
	// a save older than this field loaded, with no BeginPlay of its own.
	// An ordinary field: GZDoom writes it into the saved game.
	int sdMagFired;

	// Tics into the reload in progress (A_SD_ReloadTick counts them).
	int sdReloadTic;

	// Rounds in the magazine: what is left of it, never more than the pool
	// holds (the TT-33 and the PPSh-41 share Clip, so the other gun may
	// have spent the rounds this one counts).
	clearscope int SD_MagazineLoaded(int capacity)
	{
		int pool = Ammo1 != null ? Ammo1.Amount : 0;
		return clamp(capacity - sdMagFired, 0, pool);
	}

	// The magazine is spent and the pool can refill it: reloads on, every
	// round of the magazine fired, at least one shot left in the pool.
	// With the pool empty too this is false, and the engine's own
	// out-of-ammo switch happens as before (BALANCE.md 4.1).
	clearscope bool SD_MagazineDry(int capacity)
	{
		return SD_Reloads.On() && sdMagFired >= capacity
			&& Ammo1 != null && Ammo1.Amount >= AmmoUse1;
	}

	// A reload would put at least one round in: reloads on, the magazine
	// not full, and the pool holding more than the magazine does.
	clearscope bool SD_CanReload(int capacity)
	{
		if (!SD_Reloads.On() || Ammo1 == null)
		{
			return false;
		}
		int loaded = SD_MagazineLoaded(capacity);
		return loaded < capacity && Ammo1.Amount > loaded;
	}

	// A_WeaponReady's flags: WRF_ALLOWRELOAD lets the +reload key (R by
	// default, KEYCONF) jump to the Reload state, only when it would load.
	int SD_ReadyFlags(int capacity)
	{
		return SD_CanReload(capacity) ? WRF_ALLOWRELOAD : 0;
	}

	// The refill: as many rounds as the pool holds, up to the capacity.
	void SD_FillMagazine(int capacity)
	{
		int pool = Ammo1 != null ? Ammo1.Amount : 0;
		sdMagFired = capacity - min(capacity, pool);
	}

	// Every primary shot of these guns goes through DepleteAmmo
	// (A_FireBullets and A_FireProjectile with their default useammo), so
	// the magazine counts here and no Fire frame had to change for it. Off,
	// the magazine is left as it was.
	override bool DepleteAmmo(bool altFire, bool checkEnough, int ammouse, bool forceammouse)
	{
		if (!Super.DepleteAmmo(altFire, checkEnough, ammouse, forceammouse))
		{
			return false;
		}
		if (!altFire && SD_Reloads.On())
		{
			sdMagFired++;
		}
		return true;
	}

	// The Reload state's first frame.
	action void A_SD_BeginReload()
	{
		invoker.sdReloadTic = 0;
	}

	// One tic of the reload: the sprite's height (SD_Reloads.ReloadOffset),
	// the weapon's reload sound on tic `soundTic` (CHAN_WEAPON: nothing
	// else plays on it while the gun is down), and the magazine filled on
	// the tic the gun starts back up.
	action void A_SD_ReloadTick(int capacity, int total, int drop, int soundTic, Sound reloadSound)
	{
		invoker.sdReloadTic++;
		int t = invoker.sdReloadTic;
		A_WeaponOffset(0, SD_Reloads.ReloadOffset(t, total, drop), WOF_INTERPOLATE);
		if (t == soundTic)
		{
			A_StartSound(reloadSound, CHAN_WEAPON);
		}
		if (t == total - drop)
		{
			invoker.SD_FillMagazine(capacity);
		}
	}
}
